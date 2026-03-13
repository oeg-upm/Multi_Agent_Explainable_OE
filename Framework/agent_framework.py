from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from agno.agent import Agent, RunOutput
from agno.models.deepseek import DeepSeek
from agno.workflow import Loop, Step, Workflow
from agno.workflow.types import StepOutput

import os
import json
import subprocess
from typing import List
from pathlib import Path
import tempfile

import xml.etree.ElementTree as ET
from rdflib import Graph
from rdflib import Graph, RDF, OWL, RDFS
from rdflib.term import BNode
import requests
import argparse
from bs4 import BeautifulSoup

OOPS_API = "https://oops.linkeddata.es/rest"
REQUEST_TEMPLATE = "/home/jovyan/LLMOnto/Benchmark/OntologyConceptMatching/neon_code/templates/oops_request_template.xml"

BASE_URI = "http://www.semanticweb.org/myontology#"

OWLType = Literal[
    "owl:Class",
    "owl:ObjectProperty",
    "owl:DatatypeProperty",
]



class OWLAxiom(BaseModel):
    annotatedSource: str = Field(
        description="The local name of the subject entity this axiom annotates"
    )
    annotatedProperty: str = Field(
        description="The full URI of the OWL property"
    )
    annotatedTarget: str = Field(
        description="The raw RDF/XML block for the target"
    )

class SourceEntry(BaseModel):
    sourcetype: Literal["competency_question", "pitfall", "error_message", "other"] = Field(
        description="The type of source that triggered this change"
    )
    content: str = Field(description="The actual competency question, pitfall ID/description, or error message")


class RationaleEntry(BaseModel):
    agent: Literal[
        "Ontology Generation Agent",
        "Syntax Repair Agent", 
        "Logical Consistency Agent",
        "Pitfall Resolution Agent"
    ] = Field(description="The agent that made this change")
    change: str = Field(description="What was changed or added to this entity")
    reason: str = Field(description="Why this change was made")


class Entity(BaseModel):
    Type: OWLType = Field(description="The OWL type of the entity: owl:Class, owl:ObjectProperty, or owl:DatatypeProperty")
    Name: str = Field(description="The local name (no spaces, camelCase). Will be combined with the base URI.")
    Comment: str = Field(description="The definition of the term. Format: <rdfs:comment> definition </rdfs:comment>")
    Label: str = Field(description="Human readable label. Format: <rdfs:label> human readable label </rdfs:label>")
    Rationale: List[RationaleEntry] = Field(
        description="Ordered history of changes to this entity. Each entry records what changed and why. Always append new entries — never remove existing ones."
    )
    Source: List[SourceEntry] = Field(  # ← was str, now List[SourceEntry]
        description="Ordered list of sources (competency questions, pitfalls, errors) that triggered creation or modification. Always append new entries, never remove existing ones."
    )
    Domain: Optional[str] = None
    Range: Optional[str] = None
    Functional: Optional[str] = None
    Axiom: Optional[str] = None

    @field_validator('Source', mode='before')
    @classmethod
    def coerce_source_entries(cls, v):
        if not isinstance(v, list):
            # Was a plain string — wrap it as a single entry
            return [SourceEntry(sourcetype="other", content=str(v))]
        coerced = []
        for item in v:
            if isinstance(item, str):
                coerced.append(SourceEntry(sourcetype="other", content=item))
            elif isinstance(item, dict):
                coerced.append(SourceEntry(
                    sourcetype=item.get("sourcetype") or item.get("type", "other"),
                    content=item.get("content", str(item))
                ))
            else:
                coerced.append(item)
        return coerced

    @field_validator('Rationale', mode='before')
    @classmethod
    def coerce_rationale_entries(cls, v):
        if not isinstance(v, list):
            return [RationaleEntry(agent="Ontology Generation Agent", change="unknown", reason=str(v))]
        coerced = []
        for item in v:
            if isinstance(item, str):
                coerced.append(RationaleEntry(agent="Ontology Generation Agent", change="unknown", reason=item))
            elif isinstance(item, dict):
                coerced.append(RationaleEntry(
                    agent=item.get("agent", "Ontology Generation Agent"),
                    change=item.get("change", "unknown"),
                    reason=item.get("reason", str(item))
                ))
            else:
                coerced.append(item)
        return coerced
    
    def _serialize_axiom(self) -> str:
        if not self.Axiom:
            return ''
        source_uri = f"{BASE_URI}{self.Axiom.annotatedSource}"
        return f'''<owl:Axiom>
        <owl:annotatedSource rdf:resource="{source_uri}"/>
        <owl:annotatedProperty rdf:resource="{self.Axiom.annotatedProperty}"/>
        <owl:annotatedTarget>
            {self.Axiom.annotatedTarget}
        </owl:annotatedTarget>
        </owl:Axiom>'''

    def _serialize_rationale(self) -> str:
        if not self.Rationale:
            return '<vaem:rationale></vaem:rationale>'
        entries = "\n    ".join(
            f'[{entry.agent}] {entry.change}: {entry.reason}'
            for entry in self.Rationale
        )
        return f'<vaem:rationale>{entries}</vaem:rationale>'

    def _serialize_source(self) -> str:
        if not self.Source:
            return '<dc:source></dc:source>'
        entries = "\n    ".join(
            f'({entry.sourcetype}) {entry.content}'
            for entry in self.Source
        )
        return f'<dc:source>{entries}</dc:source>'

    def to_owl(self) -> str:
        uri = f"{BASE_URI}{self.Name}"
        rationale_xml = self._serialize_rationale()
        source_xml = self._serialize_source()
        axiom_xml = self._serialize_axiom()

        if self.Type == "owl:Class":
            lines = [f'<owl:Class rdf:about="{uri}">']
            lines.append(f'  {self.Comment}')
            lines.append(f'  {self.Label}')
            lines.append(f'  {rationale_xml}')
            lines.append(f'  {source_xml}')
            lines.append('</owl:Class>')
            if self.Axiom:
                lines.append(f'  <!-- Axiom: {self.Axiom} -->')
            

        elif self.Type == "owl:ObjectProperty":
            lines = [f'<owl:ObjectProperty rdf:about="{uri}">']
            lines.append(f'  {self.Comment}')
            lines.append(f'  {self.Label}')
            lines.append(f'  {rationale_xml}')
            lines.append(f'  {source_xml}')
            if self.Domain:
                lines.append(f'  <rdfs:domain rdf:resource="{BASE_URI}{self.Domain}"/>')
            if self.Range:
                lines.append(f'  <rdfs:range rdf:resource="{BASE_URI}{self.Range}"/>')
            if self.Functional and self.Functional.lower() == "true":
                lines.append(f'  <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#FunctionalProperty"/>')
            lines.append('</owl:ObjectProperty>')
            if self.Axiom:
                lines.append(f'  <!-- Axiom: {self.Axiom} -->')
            # if self.Axiom:
            #     lines.append(f'  <!-- Axiom: {self.Axiom} -->')
            # lines.append('</owl:ObjectProperty>')

        elif self.Type == "owl:DatatypeProperty":
            lines = [f'<owl:DatatypeProperty rdf:about="{uri}">']
            lines.append(f'  {self.Comment}')
            lines.append(f'  {self.Label}')
            lines.append(f'  {rationale_xml}')
            lines.append(f'  {source_xml}')
            if self.Domain:
                lines.append(f'  <rdfs:domain rdf:resource="{BASE_URI}{self.Domain}"/>')
            if self.Range:
                lines.append(f'  <rdfs:range rdf:resource="{self.Range}"/>')
            if self.Functional and self.Functional.lower() == "true":
                lines.append(f'  <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#FunctionalProperty"/>')
            lines.append('</owl:DatatypeProperty>')
            if self.Axiom:
                lines.append(f'  <!-- Axiom: {self.Axiom} -->')
            # if self.Axiom:
            #     lines.append(f'  <!-- Axiom: {self.Axiom} -->')
            # lines.append('</owl:DatatypeProperty>')

        else:
            raise ValueError(f"Unsupported OWL type: {self.Type}")

        return '\n'.join(lines)


class Answer(BaseModel):
    reason: str = Field(description="The reasoning process of the entire generation")
    OWL: List[Entity] = Field(description="List of ontology entities to be serialized as OWL")

    def to_owl_document(self, base_uri: str = BASE_URI) -> str:
        header = f'''<?xml version="1.0"?>
<rdf:RDF xml:base="{base_uri}"
         xmlns:owl="http://www.w3.org/2002/07/owl#"
         xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
         xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
         xmlns:dc="http://purl.org/dc/elements/1.1/"
         xmlns:vaem="http://www.linkedmodel.org/schema/vaem#">

  <owl:Ontology rdf:about="{base_uri}"/>'''

        footer = '</rdf:RDF>'

        order = ["owl:Class", "owl:ObjectProperty", "owl:DatatypeProperty"]
        grouped = {t: [] for t in order}
        for entity in self.OWL:
            grouped[entity.Type].append(entity)

        sections = []
        for owl_type in order:
            entities = grouped[owl_type]
            if entities:
                comment = f'  <!-- {owl_type} declarations -->'
                block = '\n\n'.join(entity.to_owl() for entity in entities)
                sections.append(f'{comment}\n\n{block}')

        body = '\n\n'.join(sections)
        return f'{header}\n\n{body}\n\n{footer}'
    
    
    
    
def is_owl(onto_str: str = "") -> bool:
    """
    check the root node is RDF/XML
    """
    try:
        root = ET.fromstring(onto_str)
        # root = tree.getroot()
        # Check if the root element is RDF and has the correct namespace
        return root.tag.endswith('RDF')
    except ET.ParseError:
        return False
    
    
def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")

    
def reason_ontology(onto_str: str) -> tuple[str, str]:
    """
    Reason the ontology using the Hermit reasoner.
    :param ontology_file: The path to the ontology file.
    :type ontology_file: str | Path
    :return: The reasoned ontology.
    :rtype: tuple[str, str]
    """
    # convert the ontology to OWL/XML
    ontology = Graph().parse(data=onto_str, format="xml")
    ontology.serialize(format="xml", destination="temp.xml")

    # open the ontology in the Hermit reasoner
    hermit = subprocess.run(["java", "-jar", "/home/jovyan/LLMOnto/Benchmark/OntologyConceptMatching/neon_code/hermit/HermiT.jar", '-k',
                            'temp.xml'],
                            capture_output=True,
                            text=True)

    return hermit.stdout, hermit.stderr


class OOPSValidation:
    """
    OOPS! validation of the produced ontology.
    """
    def __init__(self, onto_str:str | Path | Graph):
            
        self.ontology = onto_str
        self.oops_api = OOPS_API
        with open(REQUEST_TEMPLATE, "r") as f:
            self.request_template = f.read()

        self.request_body = self._compose_request()

    def _compose_request(self,
                         output_format: str = 'XML',
                         pitfalls: str = '') -> str:
        """
        Compose the request to the OOPS! API.
        :param output_format: The output format of the OOPS! API.
        :type output_format: str
        :param pitfalls: The pitfalls to check for expressed as a string of
                            comma-separated values.
        :type pitfalls: str
        :return: The request to the OOPS! API.
        :rtype: str
        """
        # format the ontology parameter
        formatted_ontology = f'<![CDATA[ {self.ontology} ]]></OntologyContent>'
        formatted_request = self.request_template.replace('</OntologyContent>',
                                                          formatted_ontology)

        # format the output format parameter
        if output_format not in ['XML', 'RDF/XML']:
            raise ValueError(f'Invalid output format: {output_format}')
        formatted_output = f'{output_format}</OutputFormat>'
        formatted_request = formatted_request.replace('</OutputFormat>',
                                                      formatted_output)

        # format the pitfalls parameter
        if pitfalls:
            formatted_pitfalls = f'{pitfalls}</Pitfalls>'
            formatted_request = formatted_request.replace('</Pitfalls>',
                                                          formatted_pitfalls)

        return formatted_request

    def validate(self) -> str:
        """
        Validate the ontology using the OOPS! API.
        :return: The OOPS! validation results.
        :rtype: dict
        """
        # print(self.request_body)
        try:
            response = requests.post(url=self.oops_api,
                                     data=self.request_body,
                                     allow_redirects=False).text
            # print(response)
            # format the text as xml
            response = BeautifulSoup(response, features="xml").prettify()
            return response
        except Exception as e:
            raise Exception(f"Error connecting to the OOPS! API: {e}") from e


def format_oops_nl(oops_response):
    opps_prompt = "Here is a list of oops pitfalls: \n"
    soup = BeautifulSoup(oops_response, "xml")
    pitfalls = soup.find_all("oops:Pitfall")
    # print(pitfalls)
    for pitfall in pitfalls:
        description = pitfall.find_all("oops:Description")[0].text
        try:
            affects = pitfall.find_all("oops:Affects")[0].text
            # print(affects)
        except: 
            affects = ""
        opps_prompt += description
        opps_prompt += affects
    return opps_prompt


def merge_rationale(old_owl_str: str, new_answer: Answer) -> Answer:
    """
    Preserve rationale history from the previous OWL string into the new Answer.
    Matches entities by Name and appends old rationale entries to new ones.
    """
    # Parse old rationale entries from the OWL string by Name
    old_rationale_map = {}  # Name -> List[RationaleEntry]
    old_source_map = {}     # Name -> List[SourceEntry]

    try:
        root = ET.fromstring(old_owl_str)
        ns = {
            'vaem': 'http://www.linkedmodel.org/schema/vaem#',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
        }

        for tag in ['owl:Class', 'owl:ObjectProperty', 'owl:DatatypeProperty']:
            for elem in root.findall(f'{{{tag.split(":")[1]}}}' if ':' in tag else tag, {}):
                pass

        # Simpler: just scan all elements with rdf:about
        for elem in root.iter():
            about = elem.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
            if not about:
                continue
            name = about.split('#')[-1]

            # Extract vaem:rationale text
            rationale_elem = elem.find('{http://www.linkedmodel.org/schema/vaem#}rationale')
            if rationale_elem is not None and rationale_elem.text:
                entries = []
                for line in rationale_elem.text.strip().split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    # Parse "[agent_name] change: reason"
                    import re
                    m = re.match(r'\[(\w+)\]\s+(.+?):\s+(.+)', line)
                    if m:
                        entries.append(RationaleEntry(
                            agent=m.group(1),
                            change=m.group(2),
                            reason=m.group(3)
                        ))
                    else:
                        entries.append(RationaleEntry(
                            agent="Ontology Generation Agent",
                            change="unknown",
                            reason=line
                        ))
                old_rationale_map[name] = entries

            # Extract dc:source text
            source_elem = elem.find('{http://purl.org/dc/elements/1.1/}source')
            if source_elem is not None and source_elem.text:
                entries = []
                for line in source_elem.text.strip().split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    # Parse "(sourcetype) content"
                    import re
                    m = re.match(r'\((\w+)\)\s+(.+)', line)
                    if m:
                        stype = m.group(1)
                        if stype not in ["competency_question", "pitfall", "error_message", "other"]:
                            stype = "other"
                        entries.append(SourceEntry(sourcetype=stype, content=m.group(2)))
                    else:
                        entries.append(SourceEntry(sourcetype="other", content=line))
                old_source_map[name] = entries

    except ET.ParseError as e:
        print(f"  Warning: could not parse old OWL for rationale merging: {e}")
        return new_answer

    # Merge: prepend old entries before new ones for each matching entity
    for entity in new_answer.OWL:
        if entity.Name in old_rationale_map:
            old_entries = old_rationale_map[entity.Name]
            # Avoid duplicating entries that already exist
            existing = {(e.agent, e.change) for e in entity.Rationale}
            new_old = [e for e in old_entries if (e.agent, e.change) not in existing]
            entity.Rationale = new_old + entity.Rationale

        if entity.Name in old_source_map:
            old_entries = old_source_map[entity.Name]
            existing = {(e.sourcetype, e.content) for e in entity.Source}
            new_old = [e for e in old_entries if (e.sourcetype, e.content) not in existing]
            entity.Source = new_old + entity.Source

    return new_answer

def parse_answer(response, agent_name: str) -> Answer:
    """
    Safely extract an Answer object and stamp agent_name on all RationaleEntries.
    """
    content = response.content

    if isinstance(content, Answer):
        answer = content
    elif isinstance(content, dict):
        answer = Answer(**content)
    elif isinstance(content, str):
        try:
            data = json.loads(content)
            answer = Answer(**data)
        except (json.JSONDecodeError, TypeError):
            print(f"  Warning: agent returned raw string, wrapping as fallback Answer")
            answer = Answer(
                reason="Raw string fallback — agent did not follow output_schema",
                OWL=[]
            )
    else:
        raise ValueError(f"Unexpected response.content type: {type(content)}")

    # Stamp the agent name onto every rationale entry regardless of what LLM returned
    for entity in answer.OWL:
        for entry in entity.Rationale:
            entry.agent = agent_name  # stamped server-side, always correct
    return answer



            
class NEONWorkflow(Workflow):
    """NEON-GPT Workflow following the methodology from the paper"""
    
    def __init__(self, competency_questions: str):
        super().__init__(name="NEON-GPT Workflow")
        self.cqs = competency_questions
        self.ontology_gen_agent = Agent(
            model=DeepSeek(id="deepseek-reasoner"),
            name="Ontology Generation Agent",
            role="Ontology specialist",
            instructions="You are an experienced knowledge engineer, and you are modelling a specific domain. Based on the provided competency questions, produce the ontology source code following the OWL format. \nMake it as complete as possible, and focus on the concepts, properties, domains and ranges that you think is applicable from the competency questions.\n Please generate the ontology in XML format.",
            output_schema=Answer
        )
        
        self.ontology_syntax_agent = Agent(
            model=DeepSeek(id="deepseek-reasoner"),
            name = "Syntax Repair Agent",
            role="Ontology specialist",
            instructions="You are an experienced knowledge engineer. Now please fix syntax errors in the provided RDF/XML code",
            output_schema=Answer
        )

        self.ontology_hermit_agent = Agent(
            model=DeepSeek(id="deepseek-reasoner"),
            name="Logical Consistency Agent",
            role="Ontology Debugging specialist",
            instructions="You are an experienced ontology engineer. Now you have a debugging-suggestion report for a specific ontology from HERMIT. The purpose of HERMIT is to determine whether or not the ontology is consistent and identify subsumption relationships between classes. Please carefully analyse the HERMIT report and the source code for the ontology, debug the source code ontology and generate the updated version of the ontology.",
            output_schema=Answer
        )

        self.ontology_oops_agent = Agent(
            model=DeepSeek(id="deepseek-reasoner"),
            name="Pitfall Resulotion Agent",
            role="Ontology Debugging specialist",
            instructions="You are an experienced ontology engineer. Now you have a debugging suggestion report for a specific ontology from the OOPS. The purpose of OOPS is to support ontology developers during ontology validation, which can be divided into diagnosis and repair. Please carefully analyse the OOPS report and the source code for the ontology, debug the source code ontology and generate the updated version of the ontology.",
            output_schema=Answer
        )
        
    def run(self, neon_method):
        """Execute the full NEON workflow"""
        
        # Step 1: Generate initial ontology draft (Specification & Conceptualization)
        if neon_method:
            print("Executing NEON workflow:")
            print("Step 1: Generating initial ontology draft...")
            gen_response = self.ontology_gen_agent.run(self.cqs)
            # initial_ontology = gen_response.content.OWL
            # ontology = gen_response.content.to_owl_document()
            ontology = parse_answer(gen_response, agent_name="Ontology Generation Agent").to_owl_document()
            print("Initial ontologyn draft:")
            print(ontology)
            
            while True:
                if is_owl(ontology):
                    print("Syntax validation passed")
                    break
                else:
                    ontology = self._syntax_validation_loop(ontology)
            print(ontology)
            # Step 3: Consistency checking with Hermit
            print("Step 2: Consistency checking with Hermit...")
            ontology = self._consistency_check_loop(ontology)
            while True:
                if is_owl(ontology):
                    print("Syntax validation passed")
                    break
                else:
                    ontology = self._syntax_validation_loop(ontology)
            print("Consistency checking passed")
            print(ontology)
            # Step 4: Pitfall resolution with OOPS
            print("Step 3: Pitfall resolution with OOPS...")
            ontology = self._pitfall_resolution_loop(ontology)
            while True:
                if is_owl(ontology):
                    print("Syntax validation passed")
                    break
                else:
                    ontology = self._syntax_validation_loop(ontology)
            print("Pitfall resolution completed")
            print(ontology)
        else:
            print("Executing normal workflow:")
            gen_response = self.ontology_gen_agent.run(self.cqs)
            # ontology = gen_response.content.to_owl_document()
            ontology = parse_answer(gen_response, agent_name="Ontology Generation Agent").to_owl_document()
            while True:
                if is_owl(ontology):
                    print("Syntax validation passed")
                    break
                else:
                    ontology = self._syntax_validation_loop(ontology)
            print("Syntax validation passed")
        return ontology
    
    def _syntax_validation_loop(self, ontology: str) -> str:
        try:
            root = ET.fromstring(ontology)
            return ontology  # Syntax is valid
        except ET.ParseError as e:
            print(f"  Syntax error detected: {str(e)}...")

            # Create prompt for fixing syntax errors
            syntax_prompt = f"""
            I have an OWL ontology with syntax errors. Please fix the syntax issues.

            Ontology:
            {ontology}

            Error message:
            {str(e)}

            Please return ONLY the corrected RDF/XML code.
            """

            # Use a simple agent for syntax fixing
            response = self.ontology_syntax_agent.run(syntax_prompt)
            new_answer = parse_answer(response, agent_name="Syntax Repair Agent")
            new_answer = merge_rationale(ontology, new_answer)
            ontology = new_answer.to_owl_document()
        
        return ontology
    
    def _consistency_check_loop(self, ontology: str) -> str:
        """Step 3: Check and fix consistency with Hermit"""
        stdout, stderr = reason_ontology(ontology)
            
        if stderr:
            print(f"  Consistency error detected: {stderr}...")

            # Use Hermit agent to debug
            hermit_prompt = f"""
            I have an OWL ontology with consistency errors according to the Hermit reasoner.

            Ontology:
            {ontology}

            Hermit error report:
            {stderr}

            Please analyze and fix the consistency issues.
            """

            response = self.ontology_hermit_agent.run(hermit_prompt)
            new_answer = parse_answer(response, agent_name="Logical Consistency Agent")
            new_answer = merge_rationale(ontology, new_answer)
            ontology = new_answer.to_owl_document()
        else:
            pass
        return ontology
    
    def _pitfall_resolution_loop(self, ontology: str) -> str:
        oops = OOPSValidation(ontology)
        oops_response = oops.validate()
        print(oops_response)
        opps_pitfalls = format_oops_nl(oops_response)
        oops_prompt = f"""
        I have an OWL ontology with the following OOPS pitfall report.
        Ontology:
        {ontology}
        OOPS pitfall report:
        {opps_pitfalls}
        Please analyze and fix the identified pitfalls.
        """
        response = self.ontology_oops_agent.run(oops_prompt)
        new_answer = parse_answer(response, agent_name="Pitfall Resulotion Agent")
        new_answer = merge_rationale(ontology, new_answer)
        ontology = new_answer.to_owl_document()
        return ontology
            


            
            
def final_onto(cqs_path, neon_method):
    """Execute the complete NEON-GPT workflow"""
    print("=== NEON-GPT Workflow ===")
    print("Loading competency questions...")
    with open(cqs_path, "rb") as f:
        cqs = json.load(f)
    
    start_prompt = "All competency questions are provided here:\n"
    
    for cq in cqs:
        start_prompt += cq
        start_prompt += "\n"
    
    workflow = NEONWorkflow(start_prompt)
    final_ontology = workflow.run(neon_method)
    if neon_method:
    
        if final_ontology:
            print("\n" + "="*50)
            print("WORKFLOW COMPLETED SUCCESSFULLY!")
            print("="*50)

            # Validate it
            print(f"✓ Is valid OWL: {is_owl(final_ontology)}")

            # Run final Hermit check
            stdout, stderr = reason_ontology(final_ontology)
            if not stderr:
                print("✓ Passes Hermit reasoner check")

            return final_ontology
        else:
            print("\nWorkflow failed to produce valid ontology")
            return None
    else:
        return final_ontology


def get_parser():
    parser = argparse.ArgumentParser(description="Evaluation of the generated ontology")
    parser.add_argument('--api_key', default = "xxx", help="deepseek offical api key", type=str)
    parser.add_argument('--agent_method',  default = "false", help="Flag of whether neon method is implmented", type=str)
    parser.add_argument('--cqs_file', help="the location of generated ontology file ", type=str)
    parser.add_argument('--save_file', help="the location of ground truth ontology file", type=str)
    return parser


def main():
    para_parser = get_parser()
    args = para_parser.parse_args()
    args_dict = vars(args)
    os.environ['DEEPSEEK_API_KEY'] = args_dict["api_key"]
    cqs_path = args_dict["cqs_file"]
    save_path = args_dict["save_file"]
    neon_method = str2bool(args_dict["neon_method"])
    ontology = None
    idx = 1
    while ontology is None:
        print(f"running index: {idx}")
        ontology = final_onto(cqs_path, neon_method)
        idx += 1
    with open(save_path, "w") as f:
        f.write(ontology)
        
        
main()
