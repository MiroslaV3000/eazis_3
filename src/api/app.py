from fastapi import APIRouter

from src.project_objects import neural_network, sentence_extraction


router = APIRouter(tags=["Анализатор языка текста"])



@router.get("/api/create-abstract")
async def create_abstract(url: str):
    neural_result = neural_network.create_abstract(url)
    sentence_extraction_result = sentence_extraction.create_abstract(url)
    return {
        'url': url,
        'neural_network': neural_result,
        'sentence_extraction': sentence_extraction_result
    }

@router.post("/api/save")
async def save_results_to_file(filename: str, results: dict):
    with open(f'var/{filename}.json', 'w', encoding='utf-8') as f:
        import json
        json.dump(results, f, ensure_ascii=False, indent=2)
    return True


