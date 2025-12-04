"""Tests for Internal Linker services."""

from uuid import uuid4

import pytest

from app.internal_linker import (
    BasicInternalLinker,
    SemanticInternalLinker,
    AnchorTextRewriter,
    InternalLinkOpportunity,
    RelatedArticle,
)


class TestBasicInternalLinker:
    """Tests for Basic Internal Linker using string matching."""

    @pytest.mark.asyncio
    async def test_find_link_opportunities(self):
        """Test finding link opportunities with string matching."""
        linker = BasicInternalLinker(mock_mode=True)
        
        # Set up mock articles
        mock_articles = [
            {
                "id": uuid4(),
                "title": "Article about SEO",
                "content": "This article discusses SEO best practices and keyword research techniques.",
                "target_keywords": ["SEO", "keyword research"],
            },
            {
                "id": uuid4(),
                "title": "Content Marketing Guide",
                "content": "Learn about content marketing and how SEO helps with visibility.",
                "target_keywords": ["content marketing"],
            },
        ]
        linker.set_mock_articles(mock_articles)
        
        new_article_id = uuid4()
        
        opportunities = await linker.find_link_opportunities(
            new_article_id=new_article_id,
            new_article_content="<p>New article content about marketing</p>",
            target_keywords=["SEO", "visibility"],
            workspace_id=uuid4(),
        )
        
        # Should find matches for "SEO" in both articles
        assert len(opportunities) >= 1
        for opp in opportunities:
            assert opp.to_article_id == new_article_id
            assert opp.keyword in ["SEO", "visibility"]

    @pytest.mark.asyncio
    async def test_find_keyword_matches(self):
        """Test keyword matching in content."""
        linker = BasicInternalLinker(mock_mode=True)
        
        content = "This is about SEO optimization and SEO best practices for better SEO results."
        matches = linker._find_keyword_matches(content, "SEO")
        
        # Should find multiple matches
        assert len(matches) == 3
        for match in matches:
            assert "position" in match
            assert "context" in match

    @pytest.mark.asyncio
    async def test_find_reverse_link_opportunities(self):
        """Test finding opportunities to link FROM new article TO existing."""
        linker = BasicInternalLinker(mock_mode=True)
        
        old_article_id = uuid4()
        mock_articles = [
            {
                "id": old_article_id,
                "title": "SEO Guide",
                "content": "Complete SEO guide",
                "target_keywords": ["SEO guide", "optimization"],
            },
        ]
        linker.set_mock_articles(mock_articles)
        
        new_article_content = "Check our SEO guide for more details on optimization techniques."
        
        opportunities = await linker.find_reverse_link_opportunities(
            new_article_id=uuid4(),
            new_article_content=new_article_content,
            workspace_id=uuid4(),
        )
        
        # Should find "SEO guide" and "optimization" matches
        assert len(opportunities) >= 1

    @pytest.mark.asyncio
    async def test_get_all_link_opportunities(self):
        """Test getting bidirectional link opportunities."""
        linker = BasicInternalLinker(mock_mode=True)
        
        mock_articles = [
            {
                "id": uuid4(),
                "title": "Old Article",
                "content": "Content about marketing and SEO",
                "target_keywords": ["marketing"],
            },
        ]
        linker.set_mock_articles(mock_articles)
        
        to_opps, from_opps = await linker.get_all_link_opportunities(
            new_article_id=uuid4(),
            new_article_content="This is about marketing strategies",
            target_keywords=["SEO"],
            workspace_id=uuid4(),
        )
        
        assert isinstance(to_opps, list)
        assert isinstance(from_opps, list)


class TestSemanticInternalLinker:
    """Tests for Semantic Internal Linker using embeddings."""

    @pytest.mark.asyncio
    async def test_encode_text(self):
        """Test encoding text to embeddings in mock mode."""
        linker = SemanticInternalLinker(mock_mode=True)
        
        embedding = linker.encode("This is test content about SEO")
        
        assert embedding is not None
        assert len(embedding) == 384  # Standard embedding size
        assert all(isinstance(v, float) for v in embedding)

    @pytest.mark.asyncio
    async def test_find_related_articles(self):
        """Test finding semantically related articles."""
        linker = SemanticInternalLinker(mock_mode=True)
        
        # Create mock articles with embeddings
        mock_embedding = linker.encode("SEO optimization content")
        mock_articles = [
            {
                "id": uuid4(),
                "title": "SEO Best Practices",
                "content": "SEO optimization content",
                "embedding": mock_embedding,
                "target_keywords": ["SEO"],
            },
            {
                "id": uuid4(),
                "title": "Cooking Recipes",
                "content": "How to cook pasta",
                "embedding": linker.encode("How to cook pasta"),
                "target_keywords": ["cooking"],
            },
        ]
        linker.set_mock_articles(mock_articles)
        
        new_article_id = uuid4()
        related = await linker.find_related_articles(
            new_article_id=new_article_id,
            new_article_content="SEO optimization techniques and strategies",
            workspace_id=uuid4(),
            threshold=0.3,  # Lower threshold for mock embeddings
        )
        
        assert isinstance(related, list)

    @pytest.mark.asyncio
    async def test_find_semantic_link_opportunities(self):
        """Test finding semantic link opportunities."""
        linker = SemanticInternalLinker(mock_mode=True)
        
        mock_articles = [
            {
                "id": uuid4(),
                "title": "SEO Guide",
                "content": "Complete SEO guide",
                "embedding": linker.encode("Complete SEO guide"),
                "target_keywords": ["SEO guide"],
            },
        ]
        linker.set_mock_articles(mock_articles)
        
        opportunities = await linker.find_semantic_link_opportunities(
            new_article_id=uuid4(),
            new_article_content="Learn about SEO best practices",
            target_keywords=["SEO"],
            workspace_id=uuid4(),
            threshold=0.3,
        )
        
        assert isinstance(opportunities, list)
        for opp in opportunities:
            assert isinstance(opp, InternalLinkOpportunity)

    @pytest.mark.asyncio
    async def test_process_workspace(self):
        """Test processing a workspace for internal linking."""
        linker = SemanticInternalLinker(mock_mode=True)
        
        mock_articles = [
            {
                "id": uuid4(),
                "title": "Article 1",
                "content": "Content about topic A",
                "embedding": linker.encode("Content about topic A"),
                "target_keywords": ["topic A"],
            },
            {
                "id": uuid4(),
                "title": "Article 2",
                "content": "Content about topic B",
                "embedding": linker.encode("Content about topic B"),
                "target_keywords": ["topic B"],
            },
        ]
        linker.set_mock_articles(mock_articles)
        
        result = await linker.process_workspace(
            workspace_id=uuid4(),
            threshold=0.3,
        )
        
        assert "workspace_id" in result
        assert "articles_processed" in result
        assert result["articles_processed"] == 2

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        from app.internal_linker.semantic_linker import cosine_similarity
        
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        
        similarity = cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(1.0, abs=0.01)
        
        vec3 = [0.0, 1.0, 0.0]
        similarity = cosine_similarity(vec1, vec3)
        assert similarity == pytest.approx(0.0, abs=0.01)

    def test_cosine_similarity_empty_vectors(self):
        """Test cosine similarity with empty vectors."""
        from app.internal_linker.semantic_linker import cosine_similarity
        
        assert cosine_similarity([], [1.0, 0.0]) == 0.0
        assert cosine_similarity([1.0], []) == 0.0


class TestAnchorTextRewriter:
    """Tests for AI Anchor Text Rewriter."""

    @pytest.mark.asyncio
    async def test_rewrite_sentence_with_link_mock_mode(self):
        """Test rewriting sentence with link in mock mode."""
        rewriter = AnchorTextRewriter(mock_mode=True)
        
        sentence = "SEO is important for website visibility."
        keyword = "SEO"
        target_url = "https://example.com/seo-guide"
        
        result = await rewriter.rewrite_sentence_with_link(
            sentence=sentence,
            keyword=keyword,
            target_url=target_url,
        )
        
        assert '<a href="https://example.com/seo-guide">' in result
        assert keyword in result
        
        # Verify mock response was recorded
        assert len(rewriter.mock_responses) == 1
        assert rewriter.mock_responses[0]["original"] == sentence

    @pytest.mark.asyncio
    async def test_rewrite_multiple_sentences(self):
        """Test rewriting multiple sentences."""
        rewriter = AnchorTextRewriter(mock_mode=True)
        
        sentences = [
            {
                "sentence": "SEO helps with visibility",
                "keyword": "SEO",
                "target_url": "https://example.com/seo",
            },
            {
                "sentence": "Content marketing is effective",
                "keyword": "content marketing",
                "target_url": "https://example.com/content",
            },
        ]
        
        results = await rewriter.rewrite_multiple_sentences(sentences)
        
        assert len(results) == 2
        for result in results:
            assert "original" in result
            assert "rewritten" in result
            assert "<a href=" in result["rewritten"]

    @pytest.mark.asyncio
    async def test_suggest_anchor_text_mock_mode(self):
        """Test suggesting anchor text in mock mode."""
        rewriter = AnchorTextRewriter(mock_mode=True)
        
        suggestions = await rewriter.suggest_anchor_text(
            article_title="Complete SEO Guide",
            article_content="This is a comprehensive guide to SEO...",
            target_keywords=["SEO guide", "SEO tips"],
        )
        
        assert len(suggestions) >= 1
        assert "Complete SEO Guide" in suggestions or "SEO guide" in suggestions

    def test_simple_link_insertion(self):
        """Test simple fallback link insertion."""
        rewriter = AnchorTextRewriter(mock_mode=True)
        
        result = rewriter._simple_link_insertion(
            sentence="Learn about SEO today",
            keyword="SEO",
            target_url="https://example.com/seo",
        )
        
        assert '<a href="https://example.com/seo">SEO</a>' in result

    def test_simple_link_insertion_case_insensitive(self):
        """Test case insensitive link insertion."""
        rewriter = AnchorTextRewriter(mock_mode=True)
        
        result = rewriter._simple_link_insertion(
            sentence="Learn about seo and Seo techniques",
            keyword="SEO",
            target_url="https://example.com/seo",
        )
        
        # Should replace only first occurrence
        assert result.count('<a href=') == 1

    def test_clear_mock_responses(self):
        """Test clearing mock responses."""
        rewriter = AnchorTextRewriter(mock_mode=True)
        rewriter._mock_responses = [{"test": "data"}]
        
        rewriter.clear_mock_responses()
        
        assert len(rewriter.mock_responses) == 0


class TestInternalLinkModels:
    """Tests for Internal Link data models."""

    def test_internal_link_opportunity(self):
        """Test InternalLinkOpportunity dataclass."""
        opp = InternalLinkOpportunity(
            from_article_id=uuid4(),
            to_article_id=uuid4(),
            keyword="SEO",
            position=100,
            context="...about SEO optimization...",
            similarity_score=0.85,
        )
        
        assert opp.keyword == "SEO"
        assert opp.position == 100
        assert opp.similarity_score == 0.85

    def test_related_article(self):
        """Test RelatedArticle dataclass."""
        article = RelatedArticle(
            article_id=uuid4(),
            title="SEO Guide",
            url="https://example.com/seo",
            similarity=0.9,
            target_keywords=["SEO", "optimization"],
        )
        
        assert article.title == "SEO Guide"
        assert article.similarity == 0.9
        assert len(article.target_keywords) == 2
