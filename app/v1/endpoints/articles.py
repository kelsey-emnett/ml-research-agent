from fastapi import APIRouter, HTTPException

from app.v1.repositories.articles import ArticleRepository
from app.v1.schemas.articles import ArticleInput, ArticleResponse
from app.v1.client.articles import ExtractResearchArticles
from typing import List

router = APIRouter()


@router.get(
    "/retrieve_saved_articles/",
    tags=["retrieve_saved_articles"],
    response_model=List[ArticleResponse],
)
async def retrieve_saved_articles_by_doi(doi_list: List[str]) -> List[ArticleResponse]:
    try:
        article_cls = ArticleRepository()
        results = await article_cls.get_multiple_articles_by_doi(doi_list)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving saved articles: {str(e)}",
        )


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
