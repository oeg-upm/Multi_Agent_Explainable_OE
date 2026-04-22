import argparse
from agent_framework import *

def get_parser():
    parser = argparse.ArgumentParser(description="Evaluation of the generated ontology")
    parser.add_argument('--api_key', default = "xxx", help="deepseek offical api key", type=str)
    parser.add_argument('--agent_method',  default = "true", help="Flag of whether neon method is implmented", type=str)
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
    agent_method = str2bool(args_dict["agent_method"])
    ontology = None
    idx = 1
    while ontology is None:
        print(f"running index: {idx}")
        ontology = final_onto(cqs_path, agent_method)
        idx += 1
    with open(save_path, "w") as f:
        f.write(ontology)
        
        
main()