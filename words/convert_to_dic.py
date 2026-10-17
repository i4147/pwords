import json
import sys

def convert_json_array_to_dict(input_file, output_file):
    """
    Convert a JSON array of single-key objects to a single dictionary object.
    
    Args:
        input_file (str): Path to input JSON file
        output_file (str): Path to output JSON file
    """
    try:
        # Read the input JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if the input is a list
        if not isinstance(data, list):
            raise ValueError("Input JSON must be an array/list")
        
        # Convert array of objects to a single dictionary
        result = {}
        for item in data:
            if isinstance(item, dict) and len(item) == 1:
                # Extract the key and value from each single-item dictionary
                key, value = next(iter(item.items()))
                result[key] = value
            else:
                print(f"Warning: Skipping invalid item: {item}")
        
        # Write the output JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully converted {input_file} to {output_file}")
        print(f"Total entries converted: {len(result)}")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    # Set input and output filenames
    input_filename = "input.json"  # Change this to your input filename
    output_filename = "output.json"  # Change this to your desired output filename
    
    # If command-line arguments are provided, use them
    if len(sys.argv) >= 2:
        input_filename = sys.argv[1]
    if len(sys.argv) >= 3:
        output_filename = sys.argv[2]
    
    convert_json_array_to_dict(input_filename, output_filename)

if __name__ == "__main__":
    main()