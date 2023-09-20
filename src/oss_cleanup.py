import argparse
import json

def main():
    parser = argparse.ArgumentParser(
        description='Cleanup Github User Mapping File')
    parser.add_argument(
        '--config_file', 
        dest='config_file',
        help='The path to the mapping file.', 
        type=str)
    
    args = parser.parse_args()

    # Get the Config file
    config_items = json.load(open(args.config_file))




if __name__ == '__main__':
    main()