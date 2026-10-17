#!/usr/bin/env python3
import sys
import json
import re
import html
from html.parser import HTMLParser

class WebsterParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.entries = []
        self.current_entry = None
        self.current_tag = None
        self.tag_stack = []
        self.text_buffer = []
        
    def handle_starttag(self, tag, attrs):
        self.tag_stack.append(tag)
        self.current_tag = tag
        if tag == 'p':
            self.current_entry = {
                'word': '',
                'pronunciation': '',
                'definition': '',
                'part_of_speech': '',
                'etymology': '',
                'notes': []
            }
        elif tag == 'col':
            if self.current_entry:
                self.current_entry['word'] = ''
        elif tag == 'cd':
            if self.current_entry:
                self.current_entry['definition'] = ''
        elif tag == 'i':
            # Italic text often contains etymology
            pass
        elif tag == 'b':
            # Bold text is usually the word
            pass
            
    def handle_endtag(self, tag):
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()
        
        if tag == 'p' and self.current_entry:
            # Clean up the entry
            for key in self.current_entry:
                if isinstance(self.current_entry[key], str):
                    self.current_entry[key] = self.current_entry[key].strip()
            if self.current_entry['word']:  # Only add if we have a word
                self.entries.append(self.current_entry)
            self.current_entry = None
        elif tag == 'col':
            pass
        elif tag == 'cd':
            pass
            
        self.current_tag = self.tag_stack[-1] if self.tag_stack else None
        
    def handle_data(self, data):
        if not self.current_entry:
            return
            
        # Clean the data
        data = html.unescape(data)
        
        if self.current_tag == 'b' and 'col' in self.tag_stack:
            # This is the word
            self.current_entry['word'] += data
        elif self.current_tag == 'i' and 'col' in self.tag_stack:
            # Could be pronunciation or other info in the header
            if not self.current_entry['pronunciation']:
                self.current_entry['pronunciation'] = data
            else:
                self.current_entry['pronunciation'] += ' ' + data
        elif self.current_tag == 'i' and 'cd' in self.tag_stack:
            # Italic in definition often indicates etymology
            if not self.current_entry['etymology']:
                self.current_entry['etymology'] = data
            else:
                self.current_entry['etymology'] += ' ' + data
        elif 'cd' in self.tag_stack:
            # This is part of the definition
            self.current_entry['definition'] += data
        elif 'col' in self.tag_stack:
            # This might be pronunciation or part of speech in the header
            if self.current_entry['word']:
                # After the word, before the definition
                if not self.current_entry['pronunciation']:
                    self.current_entry['pronunciation'] = data
                else:
                    self.current_entry['pronunciation'] += ' ' + data
        else:
            # Regular text, might be part of speech or notes
            data = data.strip()
            if data and self.current_entry:
                # Check if it looks like a part of speech
                pos_pattern = r'^(n\.|v\.|adj\.|adv\.|prep\.|conj\.|interj\.|pron\.|art\.|num\.)'
                if re.match(pos_pattern, data, re.IGNORECASE):
                    self.current_entry['part_of_speech'] = data
                elif data.startswith('[') and data.endswith(']'):
                    # This is a note like [Obs.] or [Archaic]
                    self.current_entry['notes'].append(data)
                elif data:
                    # Add to definition if we have one, otherwise it's a note
                    if self.current_entry['definition']:
                        self.current_entry['definition'] += ' ' + data
                    else:
                        self.current_entry['notes'].append(data)

def parse_webster_file(filename):
    """Parse the Webster dictionary file and return a list of entries."""
    
    # Read the file
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # The file might have multiple entries per line or span multiple lines
    # First, let's split by <p> tags to get individual entries
    entries = []
    
    # Find all <p>...</p> blocks
    p_pattern = re.compile(r'<p>(.*?)</p>', re.DOTALL)
    
    for match in p_pattern.finditer(content):
        entry_html = '<p>' + match.group(1) + '</p>'
        parser = WebsterParser()
        parser.feed(entry_html)
        entries.extend(parser.entries)
    
    # If no <p> tags found, try line by line
    if not entries:
        for line in content.split('\n'):
            line = line.strip()
            if line and '<col>' in line:
                if not line.startswith('<p>'):
                    line = '<p>' + line
                if not line.endswith('</p>'):
                    line = line + '</p>'
                parser = WebsterParser()
                parser.feed(line)
                entries.extend(parser.entries)
    
    return entries

def clean_entry(entry):
    """Clean up an entry by removing extra whitespace and empty fields."""
    cleaned = {}
    for key, value in entry.items():
        if isinstance(value, list):
            value = [v.strip() for v in value if v.strip()]
            if value:  # Only include non-empty lists
                cleaned[key] = value
        elif isinstance(value, str):
            value = ' '.join(value.split())  # Normalize whitespace
            if value:  # Only include non-empty strings
                cleaned[key] = value
    return cleaned

def main():
    if len(sys.argv) != 2:
        print("Usage: python webster_to_json.py <input_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    print(f"Parsing {input_file}...")
    
    try:
        entries = parse_webster_file(input_file)
        
        # Clean up entries
        cleaned_entries = []
        for entry in entries:
            cleaned = clean_entry(entry)
            if cleaned.get('word'):  # Only include entries with a word
                cleaned_entries.append(cleaned)
        
        # Create output filename
        output_file = input_file.rsplit('.', 1)[0] + '.json'
        
        # Write JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_entries, f, indent=2, ensure_ascii=False)
        
        print(f"Converted {len(cleaned_entries)} entries to {output_file}")
        
        # Show a sample entry
        if cleaned_entries:
            print("\nSample entry:")
            print(json.dumps(cleaned_entries[0], indent=2, ensure_ascii=False))
            
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()