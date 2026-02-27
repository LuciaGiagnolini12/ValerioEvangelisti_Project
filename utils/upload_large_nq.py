#!/usr/bin/env python3
"""
Aggiunge TUTTE le risorse collegate + RELAZIONI INVERSE

Include:
- Livello 1: proprietà dei soggetti già presenti
- Livello 2: risorse collegate (TechnicalMetadata, Activity, ecc.)
- INVERSE: triple dove i nodi safe sono OGGETTO
"""

import sys

OUTPUT_GRAPH = "<http://ficlit.unibo.it/ArchivioEvangelisti/revision_safe>"

FOLLOW_PREDICATES = {
    "<https://www.ica.org/standards/RiC/ontology#hasOrHadInstantiation>",
    "<http://w3id.org/bodi#hasTechnicalMetadata>",
    "<http://w3id.org/bodi#hasTechnicalMetadataType>",
    "<http://w3id.org/bodi#hasTechnicalDescription>",
    "<http://w3id.org/bodi#generatedBy>",
    "<https://www.ica.org/standards/RiC/ontology#isRelatedTo>",
    "<http://w3id.org/bodi#hasSameHashCodeAs>",
    "<http://w3id.org/bodi#hasHashCode>",
    "<https://www.ica.org/standards/RiC/ontology#isOrWasPerformedBy>",
    "<https://www.ica.org/standards/RiC/ontology#occurredAtDate>",
    "<https://www.ica.org/standards/RiC/ontology#hasExtent>",
    "<http://w3id.org/bodi#hasOrHadSupervisor>",
    "<http://w3id.org/bodi#hasHumanValidation>",
    "<https://www.ica.org/standards/RiC/ontology#isOrWasPartOf>",
}

def extract_spo(line):
    try:
        parts = []
        pos = 0
        for _ in range(3):
            start = line.find('<', pos)
            if start == -1:
                return None, None, None
            end = line.find('>', start)
            if end == -1:
                return None, None, None
            parts.append(line[start:end+1])
            pos = end + 1
        if len(parts) >= 3:
            return parts[0], parts[1], parts[2]
    except:
        pass
    return None, None, None

def replace_graph(line):
    line = line.rstrip()
    if line.endswith(' .'):
        line = line[:-2]
    elif line.endswith('.'):
        line = line[:-1]
    line = line.rstrip()
    
    last_gt = line.rfind('>')
    if last_gt == -1:
        return f"{line} {OUTPUT_GRAPH} .\n"
    last_lt = line.rfind('<', 0, last_gt)
    if last_lt == -1:
        return f"{line} {OUTPUT_GRAPH} .\n"
    
    base = line[:last_lt].rstrip()
    return f"{base} {OUTPUT_GRAPH} .\n"

print("=" * 80)
print("AGGIUNTA RISORSE + RELAZIONI INVERSE")
print("=" * 80)
print()

# FASE 1: Analisi esistente
print("FASE 1: Analisi revision_safe.nq...")
existing_subjects = set()
existing_objects = set()
existing_triples = set()

with open("revision_safe.nq", 'r') as f:
    for line in f:
        s, p, o = extract_spo(line)
        if s and p and o:
            existing_subjects.add(s)
            if o.startswith('<') and o.endswith('>'):
                existing_objects.add(o)
            existing_triples.add((s, p, o))

print(f"  Soggetti:  {len(existing_subjects):,}")
print(f"  Oggetti:   {len(existing_objects):,}")
print(f"  Triple:    {len(existing_triples):,}")
print()

# FASE 2: Trova risorse collegate
print("FASE 2: Identificazione risorse collegate...")
level2_subjects = set()
processed = 0

with open("full_export_dedup.nq", 'r') as f:
    for line in f:
        s, p, o = extract_spo(line)
        processed += 1
        
        if s and p and o:
            if s in existing_subjects and p in FOLLOW_PREDICATES:
                if o.startswith('<') and o.endswith('>'):
                    level2_subjects.add(o)
        
        if processed % 5000000 == 0:
            print(f"  {processed // 1000000}M righe... ({len(level2_subjects):,} risorse)")

print(f"  Risorse trovate: {len(level2_subjects):,}")
print()

# FASE 3: Estrazione con INVERSE
print("FASE 3: Estrazione triple (DIRETTE + INVERSE)...")
all_safe_nodes = existing_subjects | existing_objects | level2_subjects

print(f"  Nodi safe totali: {len(all_safe_nodes):,}")
print()
print("  Estrae triple dove:")
print("    ✅ Soggetto è safe (proprietà dirette)")
print("    ✅ Oggetto è safe (relazioni inverse)")
print()

extracted_direct = 0
extracted_inverse = 0
skipped_dup = 0
processed = 0

with open("full_export_dedup.nq", 'r') as f_in:
    with open("revision_safe.nq", 'a') as f_out:
        for line in f_in:
            s, p, o = extract_spo(line)
            processed += 1
            
            if s and p and o:
                # Estrai se:
                # 1. Soggetto è safe (proprietà dirette)
                # 2. Oggetto è safe E è URI (relazioni inverse)
                is_subject_safe = s in all_safe_nodes
                is_object_safe = (o.startswith('<') and o.endswith('>') and o in all_safe_nodes)
                
                if is_subject_safe or is_object_safe:
                    if (s, p, o) not in existing_triples:
                        f_out.write(replace_graph(line))
                        
                        if is_subject_safe:
                            extracted_direct += 1
                        if is_object_safe and not is_subject_safe:
                            extracted_inverse += 1
                        
                        total = extracted_direct + extracted_inverse
                        if total % 50000 == 0:
                            print(f"    {total:,} (dirette: {extracted_direct:,}, inverse: {extracted_inverse:,})...")
                    else:
                        skipped_dup += 1
            
            if processed % 5000000 == 0:
                print(f"    Processate {processed // 1000000}M righe...")

print()
print("=" * 80)
print("✅ COMPLETATO!")
print("=" * 80)
print(f"Nodi safe totali:     {len(all_safe_nodes):,}")
print(f"Triple già presenti:  {len(existing_triples):,}")
print(f"Triple dirette:       {extracted_direct:,}")
print(f"Triple inverse:       {extracted_inverse:,}")
print(f"Triple aggiunte TOT:  {extracted_direct + extracted_inverse:,}")
print(f"Duplicate saltate:    {skipped_dup:,}")
print()
print("📁 File: revision_safe.nq")
print()
print("Esempi relazioni inverse incluse:")
print("  - <Inst2> hasSameHashCodeAs <Inst1>  (se Inst1 è safe)")
print("  - <Record2> isRelatedTo <Work1>      (se Work1 è safe)")
print("  - <Activity> isOrWasPerformedBy <Software>  (se Software è safe)")
print("=" * 80)