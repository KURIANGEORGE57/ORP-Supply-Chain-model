# backend/app/utils/canonicalize.py
import json
from typing import Any, Dict

def canonical_json(obj: Any) -> str:
    """
    Deterministic JSON canonicalization for signatures.
    Uses sorted keys, no whitespace, consistent encoding.
    RFC 8785 inspired (JCS - JSON Canonicalization Scheme).
    """
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def canonicalize_assertion(assertion_data: Dict) -> str:
    """Canonicalize assertion for signature verification."""
    canonical_data = {
        'id': assertion_data['id'],
        'batch_id': assertion_data['batch_id'],
        'agent_id': assertion_data['agent_id'],
        'schema_id': assertion_data['schema_id'],
        'timestamp': assertion_data['timestamp'].isoformat() if hasattr(assertion_data['timestamp'], 'isoformat') else assertion_data['timestamp'],
        'location_gps': assertion_data.get('location_gps', ''),
        'content_data': assertion_data['content_data']
    }
    return canonical_json(canonical_data)

def canonicalize_evaluation(evaluation_data: Dict) -> str:
    """Canonicalize evaluation for signature verification."""
    canonical_data = {
        'id': evaluation_data['id'],
        'assertion_id': evaluation_data['assertion_id'],
        'agent_id': evaluation_data['agent_id'],
        'timestamp': evaluation_data['timestamp'].isoformat() if hasattr(evaluation_data['timestamp'], 'isoformat') else evaluation_data['timestamp'],
        'result': evaluation_data['result'],
        'notes': evaluation_data.get('notes', '')
    }
    return canonical_json(canonical_data)

def compute_enactment_digest(assertion_data: Dict, evaluation_data: Dict, metadata: Dict) -> str:
    """Compute canonical digest for enactment (blockchain anchor)."""
    import hashlib

    canonical_data = {
        'assertion': assertion_data,
        'evaluation': evaluation_data,
        'metadata': metadata
    }
    canonical_str = canonical_json(canonical_data)
    return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
