from rdflib import Graph, RDF, OWL, RDFS
from rdflib.term import BNode
# Parse the  rdf into ontology file
from rdflib import Graph
from sentence_transformers import SentenceTransformer, util
from langchain_ollama import OllamaEmbeddings
import difflib
import textdistance
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from redundancy import *

import re
import os
import json
import argparse
from collections import defaultdict


import nltk
from nltk.corpus import wordnet as wn

nltk.download('wordnet')

nltk.download('omw-1.4') #multilingual wordnet


def get_class_name(uri, graph):
    """Prefer rdfs:label@en, fallback to any label, then URI local name"""

    labels = list(graph.objects(uri, RDFS.label))

    for l in labels:
        if hasattr(l, "language") and l.language == "en":
            return str(l)

    if labels:
        return str(labels[0])

    uri_str = str(uri)
    if '#' in uri_str:
        return uri_str.split('#')[-1]
    else:
        return uri_str.split('/')[-1]

def _iri_local_name(iri: str) -> str:
    """Extract local name from an IRI."""
    return iri.split("#")[-1] if "#" in iri else iri.split("/")[-1]


def _rdflib_extract(file_path: str, fmt: str) -> list:
    """Parse with RDFLib using the given format string; return class name list or raise."""
    g = Graph()
    g.parse(file_path, format=fmt)
    classes = sorted(
        cls for cls in g.subjects(RDF.type, OWL.Class)
        if not isinstance(cls, BNode)
    )
    return [get_class_name(uri, g) for uri in classes]


def extract_classes_from_owlxml(file_path):
    """
    Fallback: parse RDF/XML-style OWL (.owl / .rdf) directly via xml.etree.
    Handles files where classes are declared as <owl:Class rdf:about="..."/>.
    """
    import xml.etree.ElementTree as ET

    OWL_NS  = "http://www.w3.org/2002/07/owl#"
    RDF_NS  = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    RDFS_NS = "http://www.w3.org/2000/01/rdf-schema#"
    XML_NS  = "http://www.w3.org/XML/1998/namespace"

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"[extract_classes_from_owlxml] XML parse error: {e}")
        return []

    names = []
    for elem in root.iter(f"{{{OWL_NS}}}Class"):
        iri = elem.get(f"{{{RDF_NS}}}about") or elem.get(f"{{{RDF_NS}}}ID")
        if not iri:
            continue  # skip anonymous classes (BNode)

        en_label = any_label = None
        for lbl in elem.findall(f"{{{RDFS_NS}}}label"):
            text = (lbl.text or "").strip()
            if not text:
                continue
            lang = lbl.get(f"{{{XML_NS}}}lang")
            if lang == "en":
                en_label = text
                break
            if any_label is None:
                any_label = text

        name = en_label or any_label or _iri_local_name(iri)
        if name:
            names.append(name)

    return sorted(set(names))


def extract_classes_from_owl_functional(file_path):
    import xml.etree.ElementTree as ET

    OWL_NS = "http://www.w3.org/2002/07/owl#"
    XML_NS = "http://www.w3.org/XML/1998/namespace"

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"[extract_classes_from_owl_functional] XML parse error: {e}")
        return []

    # ── Step 1: collect declared class IRIs and abbreviatedIRIs ────────────
    # key: IRI string or abbreviatedIRI string  →  value: local name fallback
    class_ids = {}   # id_str -> local_name_fallback

    for decl in root.iter(f"{{{OWL_NS}}}Declaration"):
        cls_elem = decl.find(f"{{{OWL_NS}}}Class")
        if cls_elem is None:
            continue
        iri = cls_elem.get("IRI")
        abbr = cls_elem.get("abbreviatedIRI")
        if iri:
            class_ids[iri] = _iri_local_name(iri)
        elif abbr:
            # e.g. "schema:Person" → local name is "Person"
            local = abbr.split(":")[-1] if ":" in abbr else abbr
            class_ids[abbr] = local

    if not class_ids:
        return []

    # ── Step 2: collect rdfs:label from AnnotationAssertion blocks ─────────
    # label_map: id_str -> {"en": ..., "any": ...}
    label_map = {}

    for ann in root.iter(f"{{{OWL_NS}}}AnnotationAssertion"):
        prop = ann.find(f"{{{OWL_NS}}}AnnotationProperty")
        if prop is None:
            continue
        prop_abbr = prop.get("abbreviatedIRI", "")
        prop_iri  = prop.get("IRI", "")
        is_label  = (prop_abbr == "rdfs:label" or
                     prop_iri == "http://www.w3.org/2000/01/rdf-schema#label")
        if not is_label:
            continue

        # subject: <IRI> or <AbbreviatedIRI>
        subj_iri  = ann.find(f"{{{OWL_NS}}}IRI")
        subj_abbr = ann.find(f"{{{OWL_NS}}}AbbreviatedIRI")
        subj = (subj_iri.text if subj_iri is not None else
                subj_abbr.text if subj_abbr is not None else None)
        if not subj:
            continue

        # literal value
        lit = ann.find(f"{{{OWL_NS}}}Literal")
        if lit is None or not (lit.text or "").strip():
            continue
        text = lit.text.strip()
        lang = lit.get(f"{{{XML_NS}}}lang", "")

        if subj not in label_map:
            label_map[subj] = {}
        if lang == "en" and "en" not in label_map[subj]:
            label_map[subj]["en"] = text
        elif "any" not in label_map[subj]:
            label_map[subj]["any"] = text

    # ── Step 3: resolve each class id to its best name ─────────────────────
    names = []
    for id_str, local_fallback in class_ids.items():
        labels = label_map.get(id_str, {})
        name = labels.get("en") or labels.get("any") or local_fallback
        if name:
            names.append(name)

    return sorted(set(names))


def extract_classes_from_jsonld(file_path):
    """
    Parse JSON-LD (.jsonld) ontology files.
    Extracts @type == owl:Class entries, preferring rdfs:label.
    """
    OWL_CLASS_URIS = {"owl:Class", "http://www.w3.org/2002/07/owl#Class"}

    def _get_label(node):
        for key in ("rdfs:label", "http://www.w3.org/2000/01/rdf-schema#label", "label"):
            val = node.get(key)
            if val is None:
                continue
            if isinstance(val, str):
                return val
            if isinstance(val, list) and val:
                for v in val:
                    if isinstance(v, dict) and v.get("@language") == "en":
                        return v.get("@value", "")
                first = val[0]
                return first.get("@value", str(first)) if isinstance(first, dict) else str(first)
            if isinstance(val, dict):
                return val.get("@value", "")
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = data if isinstance(data, list) else data.get("@graph", [data])
    names = []
    for node in graph:
        if not isinstance(node, dict):
            continue
        types = node.get("@type", [])
        if isinstance(types, str):
            types = [types]
        if not any(t in OWL_CLASS_URIS for t in types):
            continue
        label = _get_label(node)
        if not label:
            iri = node.get("@id", "")
            label = _iri_local_name(iri) if iri else None
        if label:
            names.append(label)

    return sorted(set(names))


# RDFLib format candidates — extension-matched ones are tried first
_RDFLIB_FORMATS = [
    ("xml",     {".owl", ".rdf", ".xml"}),
    ("turtle",  {".ttl", ".turtle"}),
    ("nt",      {".nt"}),
    ("nquads",  {".nq"}),
    ("json-ld", {".jsonld", ".json"}),
    ("trig",    {".trig"}),
    ("trix",    {".trix"}),
]


def extract_classes(file_path):
    """
    Robustly extract OWL class names from ontology files.
    Supports: OWL/XML (.owl), RDF/XML (.rdf), Turtle (.ttl),
              N-Triples (.nt), N-Quads (.nq), JSON-LD (.jsonld).

    Strategy:
      1. Try RDFLib with all formats, extension-matched ones first.
      2. Fallback to direct OWL/XML etree parser for XML-family files.
      3. Fallback to custom JSON-LD parser.
    """
    ext = os.path.splitext(file_path)[1].lower()

    # ── Step 1: RDFLib with format auto-detection ───────────────────────────
    ordered_formats = sorted(_RDFLIB_FORMATS, key=lambda x: 0 if ext in x[1] else 1)
    last_error = None
    for fmt, _ in ordered_formats:
        try:
            names = _rdflib_extract(file_path, fmt)
            if names:
                print(f"[extract_classes] Parsed '{file_path}' with RDFLib format='{fmt}'")
                return names
        except Exception as e:
            last_error = e

    print(f"[extract_classes] RDFLib exhausted all formats (last error: {last_error}). Trying fallbacks.")

    # ── Step 2: OWL/XML etree fallback (RDF/XML style) ─────────────────────
    if ext in {".owl", ".rdf", ".xml", ""}:
        names = extract_classes_from_owlxml(file_path)
        if names:
            print(f"[extract_classes] Recovered {len(names)} classes via OWL/XML (RDF style) fallback.")
            return names

        # ── Step 3: OWL Functional Syntax XML fallback ──────────────────────
        names = extract_classes_from_owl_functional(file_path)
        if names:
            print(f"[extract_classes] Recovered {len(names)} classes via OWL Functional Syntax fallback.")
            return names

    # ── Step 3: JSON-LD fallback ────────────────────────────────────────────
    if ext in {".jsonld", ".json"}:
        try:
            names = extract_classes_from_jsonld(file_path)
            if names:
                print(f"[extract_classes] Recovered {len(names)} classes via JSON-LD fallback.")
                return names
        except Exception as e:
            print(f"[extract_classes] JSON-LD fallback failed: {e}")

    print(f"[extract_classes] WARNING: could not extract any classes from '{file_path}'.")
    return []

def pre_process(gen_class, ground_class, info_type, model_id=None, embedding_backend="sentence_transformers"):
    coverage_info = []       # gold -> pred
    coverage_info_new = []   # pred -> gold
    pre_gold = []
    res = []

    all_concepts = sorted(set(ground_class) | set(gen_class))

    # ========= 空列表处理 =========
    if len(ground_class) == 0 and len(gen_class) == 0:
        avg_sim = 0.0
        print(info_type)
        print(res)
        return coverage_info, coverage_info_new, res, avg_sim, all_concepts

    if len(ground_class) == 0:
        # 没有 gold，则无法做 gold->pred；但 pred->gold 的 FP 应该全罚满
        for c in gen_class:
            temp = {"pred": c, "ground": None, "sim": 0.0}
            res.append(temp)
            coverage_info_new.append({
                "Pred Concept": c,
                "Best Gold Match": None,
                "Similarity": 0.0
            })
        avg_sim = 0.0
        print(info_type)
        print(res)
        return coverage_info, coverage_info_new, res, avg_sim, all_concepts

    if len(gen_class) == 0:
        for g in ground_class:
            coverage_info.append({
                "Gold Concept": g,
                "Exact Match": "",
                "Best Candidate Match": None,
                "Similarity": 0.0
            })
        avg_sim = 0.0
        print(info_type)
        print(res)
        return coverage_info, coverage_info_new, res, avg_sim, all_concepts

    # ========= semantic =========
    if model_id and info_type == "semantic":

        if embedding_backend == "sentence_transformers":
            #1
            encoder = SentenceTransformer(model_id)
            ground_embed = encoder.encode(ground_class, convert_to_tensor=True)
            gen_embed    = encoder.encode(gen_class,    convert_to_tensor=True)
            encoder = OllamaEmbeddings(model=model_id)
            all_texts = ground_class + gen_class
            embeddings = encoder.embed_documents(all_texts)
            import torch
            ground_embed = torch.tensor(embeddings[:len(ground_class)])
            gen_embed    = torch.tensor(embeddings[len(ground_class):])

        # Step 1: gold -> pred
        for idx_g, g in enumerate(ground_class):
            sims = util.cos_sim(ground_embed[idx_g], gen_embed)[0]
            best_idx = sims.argmax()
            coverage_info.append({
                "Gold Concept": g,
                "Exact Match": "",
                "Best Candidate Match": gen_class[best_idx],
                "Similarity": round(float(sims[best_idx]), 3)
            })

        # Step 2: pred -> gold
        for idx_p, p in enumerate(gen_class):
            sims = util.cos_sim(gen_embed[idx_p], ground_embed)[0]
            best_idx = sims.argmax()
            temp = {
                "pred": p,
                "ground": ground_class[best_idx],
                "sim": round(float(sims[best_idx]), 3)
            }
            res.append(temp)
            coverage_info_new.append({
                "Pred Concept": p,
                "Best Gold Match": ground_class[best_idx],
                "Similarity": round(float(sims[best_idx]), 3)
            })

    # ========= lexical =========
    else:
        for g in ground_class:
            exact = g in gen_class
            best_match, best_score = None, 0.0
            for c in gen_class:
                if info_type == "sequence_match":
                    sim = difflib.SequenceMatcher(None, g, c).ratio()
                else:
                    print("Metric type is not proper defined.")
                    sim = 0.0
                if sim > best_score:
                    best_score, best_match = sim, c

            coverage_info.append({
                "Gold Concept": g,
                "Exact Match": "yes" if exact else "",
                "Best Candidate Match": best_match,
                "Similarity": round(best_score, 3)
            })

        # pred -> gold
        for c in gen_class:
            best_ground, best_score = None, 0.0
            for g in ground_class:
                if info_type == "sequence_match":
                    sim = difflib.SequenceMatcher(None, c, g).ratio()
                else:
                    print("Metric type is not proper defined.")
                    sim = 0.0
                if sim > best_score:
                    best_score, best_ground = sim, g

            temp = {"pred": c, "ground": best_ground, "sim": round(best_score, 3)}
            res.append(temp)
            coverage_info_new.append({
                "Pred Concept": c,
                "Best Gold Match": best_ground,
                "Similarity": round(best_score, 3)
            })

    avg_sim = sum(item["Similarity"] for item in coverage_info) / len(ground_class) if len(ground_class) else 0.0
    print(info_type)
    print(res)
    return coverage_info, coverage_info_new, res, avg_sim, all_concepts

def normalize(concept):
    return concept.lower().strip().replace('_', ' ').replace('-', ' ')


        

def cal_metrics(gen_class, ground_class, info_type, model_id=None, embedding_backend="sentence_transformers"):
    if info_type == "hard_match":
        all_concepts = sorted(set(ground_class) | set(gen_class))
        y_true = [1 if c in ground_class else 0 for c in all_concepts]
        y_pred = [1 if c in gen_class else 0 for c in all_concepts]

        avg_sim = len(set(gen_class) & set(ground_class)) / len(ground_class) if len(ground_class) else 0.0
        accuracy  = accuracy_score(y_true, y_pred) if len(all_concepts) else 0.0
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall    = recall_score(y_true, y_pred, zero_division=0)
        f1        = f1_score(y_true, y_pred, zero_division=0)

    else:
        coverage_info, coverage_info_new, res, avg_sim, all_concepts = pre_process(
            gen_class, ground_class, info_type, model_id, embedding_backend
        )


        TP_recall = sum(item["Similarity"] for item in coverage_info)
        FN        = sum(1 - item["Similarity"] for item in coverage_info)



        TP_precision = sum(item["sim"] for item in res)
        FP           = sum(1 - item["sim"] for item in res)

        print(f"TP_recall={TP_recall:.3f}, TP_precision={TP_precision:.3f}, FP={FP:.3f}, FN={FN:.3f}")

       
        precision = TP_precision / (TP_precision + FP) if (TP_precision + FP) > 0 else 0.0
       
        recall    = TP_recall    / (TP_recall + FN)    if (TP_recall + FN) > 0    else 0.0
       
        accuracy  = TP_recall / len(ground_class) if len(ground_class) else 0.0

        f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        print(f"Precision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"Accuracy:  {accuracy:.4f}")
        print(f"F1-score:  {f1:.4f}")

    return avg_sim, precision, recall, accuracy, f1



def _normalize(text: str) -> str:
    
    t = (text or "").strip().lower()
    t = t.replace('_', ' ').replace('-', ' ')
    t = re.sub(r'\s+', ' ', t)
    return t

def wordnet_noun_synonyms(term: str) -> set:
    """

    """
    base = _normalize(term)
    syns = set()

    variants = {base, base.replace(' ', '_')}
    for v in variants:
        for s in wn.synsets(v, pos=wn.NOUN):
            for lemma in s.lemmas():
                name = lemma.name()
                norm = _normalize(name)
                if norm and norm != base:
                    syns.add(norm)
    return syns



def strtobool(val):
    """Conver a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return 0
    else:
        raise ValueError("invalid truth value %r" % (val,))

def get_parser():
    parser = argparse.ArgumentParser(description="Evaluation of the generated ontology")
    
    parser.add_argument('--model_id', default="sentence_transformers",
                        choices=["sentence_transformers", "ollama"],
                        help='Which embedding backend to use: "sentence_transformers" (HuggingFace) or "ollama".',
                        type=str)
    parser.add_argument('--embedding_model_id', default="all-MiniLM-L6-v2",
                        help='Embedding model id. For sentence_transformers: e.g. "all-MiniLM-L6-v2". '
                             'For ollama: e.g. "embeddinggemma". Use "," to separate multiple models.',
                        type=str)
    parser.add_argument('--generate_onto_file_path', help="the location of generated ontology file ", type=str)
    parser.add_argument('--ground_onto_file_path', help="the location of ground truth ontology file", type=str)
    parser.add_argument('--save_file_path', help="the location of the saved result that contains lexical ", type=str)
    parser.add_argument('--redundancy_folder', default="/home/jovyan/LLMOnto/Benchmark/OntologyConceptMatching/software/redundancy", help="the location of the saved result of redundancy check", type=str)
    return parser


def main():
    para_parser = get_parser()
    args = para_parser.parse_args()
    args_dict = vars(args)
    model_id = args_dict["model_id"]
    embedding_backend = args_dict["embedding_backend"]
    gen_class = extract_classes(args_dict["generate_onto_file_path"])
    ground_class = extract_classes(args_dict["ground_onto_file_path"])
    
    normalized_gen_class =  [normalize(c) for c in gen_class]
    normalized_ground_class =  [normalize(c) for c in ground_class]
    info_list = [
        "hard_match",
        "sequence_match",
        "semantic",
    ]
    result = {}
    for info_type in info_list:
    
        if info_type == "semantic":
            for _model_id in model_id.split(","):
                avg_sim, precision, recall, accuracy, f1 = cal_metrics(
                    normalized_gen_class, normalized_ground_class, info_type, _model_id, embedding_backend
                )
                info_id = info_type + "_" + _model_id
                result[info_id] = {
                    "coverage_rate": avg_sim,
                    "precision": precision,
                    "recall": recall,
                    "accuracy": accuracy,
                    "f1": f1
                }
        else:
            avg_sim, precision, recall, accuracy, f1 = cal_metrics(
                normalized_gen_class, normalized_ground_class, info_type, model_id, embedding_backend
            )
            result[info_type] = {
                "coverage_rate": avg_sim,
                "precision": precision,
                "recall": recall,
                "accuracy": accuracy,
                "f1": f1
            }
    print(result)
  


if __name__ == "__main__":
    main()