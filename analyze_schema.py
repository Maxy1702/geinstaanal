"""
JSON Schema Analyzer for Instagram Data
Analyzes structure without processing
"""
import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Any, Dict, Set
import sys
from datetime import datetime

class JSONSchemaAnalyzer:
    """Analyze JSON structure and generate schema report"""
    
    def __init__(self, json_path: Path):
        self.json_path = json_path
        self.field_tracker = defaultdict(lambda: {
            'count': 0,
            'types': Counter(),
            'null_count': 0,
            'sample_values': []
        })
        self.nested_structures = defaultdict(set)
        self.post_types = Counter()
        self.error_types = Counter()
        self.total_entries = 0
        self.valid_posts = 0
        self.error_entries = 0
        
    def analyze(self):
        """Main analysis function"""
        print("="*80)
        print("JSON SCHEMA ANALYZER")
        print("="*80)
        print(f"File: {self.json_path}")
        print(f"File size: {self.json_path.stat().st_size / 1024 / 1024:.2f} MB")
        print()
        
        # Detect format
        print("Analyzing file format...")
        file_format = self._detect_format()
        print(f"Format: {file_format}")
        print()
        
        # Parse and analyze
        print("Parsing and analyzing structure...")
        if file_format == "json_array":
            self._analyze_json_array()
        else:
            self._analyze_line_delimited()
        
        # Generate report
        self._generate_report()
    
    def _detect_format(self) -> str:
        """Detect if file is JSON array or line-delimited"""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            first_char = f.read(1)
            if first_char == '[':
                return "json_array"
            elif first_char == '{':
                return "line_delimited"
            else:
                return "unknown"
    
    def _analyze_json_array(self):
        """Analyze standard JSON array format"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                print(f"ERROR: Expected array, got {type(data)}")
                return
            
            self.total_entries = len(data)
            print(f"Total entries: {self.total_entries}")
            
            for idx, entry in enumerate(data):
                if idx % 100 == 0:
                    print(f"  Processed {idx}/{self.total_entries} entries...", end='\r')
                
                self._analyze_entry(entry)
            
            print(f"  Processed {self.total_entries}/{self.total_entries} entries... Done!")
            
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON - {e}")
        except Exception as e:
            print(f"ERROR: {e}")
    
    def _analyze_line_delimited(self):
        """Analyze line-delimited JSON format"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                for idx, line in enumerate(f):
                    if idx % 100 == 0:
                        print(f"  Processed {idx} entries...", end='\r')
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry = json.loads(line)
                        self.total_entries += 1
                        self._analyze_entry(entry)
                    except json.JSONDecodeError:
                        print(f"\nWARNING: Invalid JSON at line {idx}")
                        continue
            
            print(f"  Processed {self.total_entries} entries... Done!")
            
        except Exception as e:
            print(f"ERROR: {e}")
    
    def _analyze_entry(self, entry: Dict[str, Any], prefix: str = ""):
        """Recursively analyze entry structure"""
        
        # Check if error entry
        if 'error' in entry:
            self.error_entries += 1
            self.error_types[entry.get('error', 'unknown')] += 1
        else:
            self.valid_posts += 1
            if 'type' in entry:
                self.post_types[entry['type']] += 1
        
        # Analyze all fields
        for key, value in entry.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            # Track field
            self.field_tracker[full_key]['count'] += 1
            self.field_tracker[full_key]['types'][type(value).__name__] += 1
            
            # Handle None/null
            if value is None:
                self.field_tracker[full_key]['null_count'] += 1
            
            # Sample values (first 3)
            if len(self.field_tracker[full_key]['sample_values']) < 3:
                if isinstance(value, (str, int, float, bool)):
                    self.field_tracker[full_key]['sample_values'].append(value)
                elif isinstance(value, list):
                    self.field_tracker[full_key]['sample_values'].append(f"[array:{len(value)} items]")
                elif isinstance(value, dict):
                    self.field_tracker[full_key]['sample_values'].append(f"{{dict:{len(value)} keys}}")
            
            # Recursively analyze nested structures
            if isinstance(value, dict):
                self.nested_structures[full_key].add('dict')
                self._analyze_entry(value, prefix=full_key)
            
            elif isinstance(value, list) and value:
                self.nested_structures[full_key].add('array')
                # Analyze first item to understand array structure
                if isinstance(value[0], dict):
                    self._analyze_entry(value[0], prefix=full_key)
    
    def _generate_report(self):
        """Generate comprehensive schema report"""
        
        print("\n" + "="*80)
        print("SCHEMA ANALYSIS REPORT")
        print("="*80)
        
        # Overview
        print("\n## OVERVIEW")
        print(f"Total entries: {self.total_entries}")
        print(f"Valid posts: {self.valid_posts} ({self.valid_posts/self.total_entries*100:.1f}%)")
        print(f"Error entries: {self.error_entries} ({self.error_entries/self.total_entries*100:.1f}%)")
        
        # Error types
        if self.error_types:
            print("\n## ERROR TYPES")
            for error_type, count in self.error_types.most_common():
                print(f"  {error_type}: {count}")
        
        # Post types
        if self.post_types:
            print("\n## POST TYPES (Valid Posts)")
            for post_type, count in self.post_types.most_common():
                print(f"  {post_type}: {count} ({count/self.valid_posts*100:.1f}%)")
        
        # Field analysis
        print("\n## FIELD ANALYSIS")
        print(f"Total unique fields found: {len(self.field_tracker)}")
        print()
        
        # Top-level fields
        print("### Top-Level Fields:")
        top_level = {k: v for k, v in self.field_tracker.items() if '.' not in k}
        self._print_field_table(top_level)
        
        # Nested structures
        print("\n### Nested Structures:")
        nested = {k: v for k, v in self.field_tracker.items() if '.' in k}
        
        # Group by first level
        nested_groups = defaultdict(list)
        for key in nested.keys():
            first_level = key.split('.')[0]
            nested_groups[first_level].append(key)
        
        for group, fields in sorted(nested_groups.items()):
            print(f"\n  {group}:")
            group_fields = {k: self.field_tracker[k] for k in fields}
            self._print_field_table(group_fields, indent=4)
        
        # Required vs Optional fields
        print("\n## FIELD FREQUENCY ANALYSIS")
        print("(Fields present in all valid posts are likely required)")
        print()
        
        always_present = []
        often_present = []
        sometimes_present = []
        rarely_present = []
        
        for key, info in self.field_tracker.items():
            if '.' in key:  # Skip nested for this analysis
                continue
            
            frequency = info['count'] / self.valid_posts if self.valid_posts > 0 else 0
            
            if frequency >= 0.99:
                always_present.append((key, info['count'], frequency))
            elif frequency >= 0.75:
                often_present.append((key, info['count'], frequency))
            elif frequency >= 0.25:
                sometimes_present.append((key, info['count'], frequency))
            else:
                rarely_present.append((key, info['count'], frequency))
        
        print("### Always Present (99%+):")
        for key, count, freq in sorted(always_present):
            print(f"  {key}: {count} ({freq*100:.1f}%)")
        
        print("\n### Often Present (75-99%):")
        for key, count, freq in sorted(often_present):
            print(f"  {key}: {count} ({freq*100:.1f}%)")
        
        print("\n### Sometimes Present (25-75%):")
        for key, count, freq in sorted(sometimes_present):
            print(f"  {key}: {count} ({freq*100:.1f}%)")
        
        print("\n### Rarely Present (<25%):")
        for key, count, freq in sorted(rarely_present):
            print(f"  {key}: {count} ({freq*100:.1f}%)")
        
        # Save detailed report to file
        self._save_detailed_report()
    
    def _print_field_table(self, fields: Dict, indent: int = 0):
        """Print formatted field information"""
        indent_str = " " * indent
        
        for key, info in sorted(fields.items()):
            types_str = ", ".join([f"{t}({c})" for t, c in info['types'].items()])
            null_str = f", nulls:{info['null_count']}" if info['null_count'] > 0 else ""
            
            print(f"{indent_str}{key}:")
            print(f"{indent_str}  Count: {info['count']}{null_str}")
            print(f"{indent_str}  Types: {types_str}")
            
            if info['sample_values']:
                samples = ", ".join([str(v)[:50] for v in info['sample_values'][:2]])
                print(f"{indent_str}  Samples: {samples}")
    
    def _save_detailed_report(self):
        """Save detailed JSON schema to file"""
        output_file = self.json_path.parent / f"{self.json_path.stem}_schema_report.json"
        
        report = {
            'analysis_date': datetime.now().isoformat(),
            'source_file': str(self.json_path),
            'statistics': {
                'total_entries': self.total_entries,
                'valid_posts': self.valid_posts,
                'error_entries': self.error_entries,
                'error_types': dict(self.error_types),
                'post_types': dict(self.post_types)
            },
            'fields': {
                key: {
                    'count': info['count'],
                    'frequency': info['count'] / self.valid_posts if self.valid_posts > 0 else 0,
                    'types': dict(info['types']),
                    'null_count': info['null_count'],
                    'sample_values': info['sample_values']
                }
                for key, info in self.field_tracker.items()
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n\nDetailed schema report saved to: {output_file}")


def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print("Usage: python analyze_schema.py <path_to_json_file>")
        print("\nExample: python analyze_schema.py data/input/georgia_posts.json")
        sys.exit(1)
    
    json_path = Path(sys.argv[1])
    
    if not json_path.exists():
        print(f"ERROR: File not found: {json_path}")
        sys.exit(1)
    
    analyzer = JSONSchemaAnalyzer(json_path)
    analyzer.analyze()
    
    print("\n" + "="*80)
    print("Analysis complete!")
    print("="*80)


if __name__ == "__main__":
    main()