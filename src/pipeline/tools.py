
from langchain_core.tools import Tool
from PIL import Image
import yaml
from pathlib import Path

from src.analysis.ela import compute_ela
from src.analysis.noise import block_noise_score
from src.analysis.edges import edge_inconsistency
from src.analysis.exif import inspect_exif
from src.retrieval.simple_hash import nearest

CONFIG = yaml.safe_load(open(Path('config/config.yaml'), 'r'))


def ela_tool():
    return Tool(name="ELA", description="Error Level Analysis",
                func=lambda image_path: compute_ela(Image.open(image_path).convert('RGB'),
                                                  CONFIG['analysis']['ela_quality'],
                                                  CONFIG['analysis']['ela_threshold']))

def noise_tool():
    return Tool(name="Noise", description="Block-wise noise variance",
                func=lambda image_path: block_noise_score(Image.open(image_path).convert('RGB'),
                                                         CONFIG['analysis']['block_size']))

def edges_tool():
    return Tool(name="Edges", description="Edge inconsistency",
                func=lambda image_path: edge_inconsistency(Image.open(image_path).convert('RGB'),
                                                           CONFIG['analysis']['block_size']))

def exif_tool():
    return Tool(name="EXIF", description="EXIF metadata",
                func=lambda image_path: inspect_exif(image_path, CONFIG['scoring']['suspicious_software']))

def retrieval_tool():
    return Tool(name="Similarity", description="pHash similarity",
                func=lambda image_path: nearest(image_path, CONFIG['retrieval']['hash_index_path'], CONFIG['retrieval']['top_k']))
