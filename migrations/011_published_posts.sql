-- Migration: Published Posts Table for Publishing Engine
-- Version: 011
-- Description: Tables for tracking manually published posts

SET search_path TO autoseo, public;

-- Published posts table
CREATE TABLE IF NOT EXISTS published_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID REFERENCES articles(id) ON DELETE SET NULL,
    site_id UUID REFERENCES sites(id) ON DELETE SET NULL,
    wp_post_id INTEGER,
    url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'manual', -- 'manual' | 'auto' | 'pending'
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for published_posts
CREATE INDEX IF NOT EXISTS idx_published_posts_article_id ON published_posts(article_id);
CREATE INDEX IF NOT EXISTS idx_published_posts_site_id ON published_posts(site_id);
CREATE INDEX IF NOT EXISTS idx_published_posts_status ON published_posts(status);
CREATE INDEX IF NOT EXISTS idx_published_posts_published_at ON published_posts(published_at);

-- Comments
COMMENT ON TABLE published_posts IS 'Tracking of published articles to external sites';
COMMENT ON COLUMN published_posts.article_id IS 'Reference to the original article';
COMMENT ON COLUMN published_posts.site_id IS 'Reference to the site where article was published';
COMMENT ON COLUMN published_posts.wp_post_id IS 'WordPress post ID if published to WordPress';
COMMENT ON COLUMN published_posts.url IS 'Public URL of the published post';
COMMENT ON COLUMN published_posts.status IS 'Publishing status: manual (copy-paste), auto (API), pending';
COMMENT ON COLUMN published_posts.published_at IS 'When the post was published';
