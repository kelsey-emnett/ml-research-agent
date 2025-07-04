from fastapi import APIRouter, HTTPException
from app.v1.schemas.download_articles import ArticleInput, ArticleResponse
from app.v1.client.download_articles import ExtractResearchArticles
from typing import List

router = APIRouter()


@router.post(
    "/search_download_articles/",
    tags=["search_download_articles"],
    response_model=List[ArticleResponse],
)
async def retrieve_articles(request: ArticleInput) -> List[ArticleResponse]:
    try:
        extract_cls = ExtractResearchArticles()
        results = await extract_cls.search_and_download_open_papers(request)

        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching and downloading articles: {str(e)}",
        )
