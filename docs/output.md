
## Generated Ontology Structure

The MASEO pipeline generates ontology follows the RDF/XML format, as a series of ontology entity. Each generated ontology entity is a structured object with the following fields:

| Field | Definition | Example value |
|-------|-----------|---------------|
| **Type** (`rdf:type`) | Indicates whether the entity is an `owl:Class`, `owl:ObjectProperty`, or `owl:DatatypeProperty`. | `:Player rdf:type owl:Class;` `:hasUsername rdf:type owl:DatatypeProperty` |
| **Label** (`rdfs:label`) | Provides a human-readable name for the entity. | `"Player"` ; `"has username"` |
| **Comment** (`rdfs:comment`) | Provides a textual description of the meaning of the entity. | `"A person who plays games."` ; `"Relates a player to the player's username."` |
| **Rationale** (`vaem:rationale`) | Records the justification for entity creation or modification across refinement iterations. | `"Derived from CQ [number] about the username of a player."` |
| **Source** (`dc:Source`) | Records the CQ or validation feedback from which the entity or revision was derived. | `"What is the username of the player?"` |
| **Subclass of** (`rdfs:subClassOf`) | (Classes only) Records subclass relations or logical restrictions involving the class. | `:Player rdfs:SubClassOf :Human` |
| **Disjointness** (`owl:disjointWith`) | (Classes only) Declares that two classes are mutually exclusive, meaning that no individual can belong to both classes at the same time. | `:Player owl:disjointWith :Game` |
| **Domain** (`rdfs:domain`) | (Properties only) Specifies the class to which a property applies. | `:hasUsername rdfs:domain :Player` |
| **Range** (`rdfs:range`) | (Properties only) Specifies the value type or class associated with a property. | `:hasUsername rdfs:range xsd:string` |
| **Other Axioms** | Captures logical constraints as structured XML comments to preserve modeling intent. | `<!-- Axiom: Disjoint with Game -->` (captured as comments) |

### Example output

```xml
<owl:Class rdf:about="http://www.semanticweb.org/myontology#Player">
  <dc:source>CQ1, CQ3; HermiT: conflict; OOPS P10</dc:source>
  <vaem:rationale>
    [Logical Consistency Agent] Fixed subClassOf error;
    [Ontology Pitfall Agent] Added disjointness.
  </vaem:rationale>
  <owl:disjointWith rdf:resource='#GameEvent'/>
</owl:Class>

<owl:ObjectProperty rdf:about="http://www.semanticweb.org/myontology#triggersEvent">
  <rdfs:domain rdf:resource="http://www.semanticweb.org/myontology#Player"/>
  <rdfs:range rdf:resource="http://www.semanticweb.org/myontology#GameEvent"/>
  <dc:source>HermiT: introduced to resolve Player unsatisfiability</dc:source>
  <vaem:rationale>[Logical Consistency Agent] Created to correctly model player-event relationship.</vaem:rationale>
</owl:ObjectProperty>
```