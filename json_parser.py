"""
Instagram JSON Parser - Production Version
Based on analyzed schema
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PostNormalizer:
    """Normalize Instagram post data based on schema analysis"""
    
    @staticmethod
    def normalize_post(raw_post: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw Instagram JSON to normalized structure
        
        Handles:
        - Single images, carousels (Sidecar), and videos
        - Comment extraction (firstComment + latestComments)
        - Hidden likes (-1 → None)
        - Carousel image merging
        """
        
        # Basic post info
        post_id = raw_post['id']
        post_type = raw_post['type']
        
        # Owner info
        owner = {
            'username': raw_post['ownerUsername'],
            'full_name': raw_post.get('ownerFullName', ''),
            'user_id': raw_post.get('ownerId', ''),
            'profile_url': raw_post.get('inputUrl', '')
        }
        
        # Content
        content = {
            'caption': raw_post.get('caption', ''),
            'hashtags': raw_post.get('hashtags', []),
            'mentions': raw_post.get('mentions', []),
        }
        
        # Engagement
        likes = raw_post.get('likesCount', 0)
        engagement = {
            'likes': None if likes == -1 else likes,  # Hidden likes → None
            'likes_hidden': likes == -1,
            'comments_count': raw_post.get('commentsCount', 0),
        }
        
        # Video-specific
        if post_type == 'Video':
            engagement['video_views'] = raw_post.get('videoViewCount', 0)
            engagement['video_plays'] = raw_post.get('videoPlayCount')
            content['video_duration'] = raw_post.get('videoDuration')
            content['video_url'] = raw_post.get('videoUrl')
        
        # Extract images (main + carousel children)
        images = PostNormalizer._extract_all_images(raw_post)
        
        # Extract comments (firstComment + latestComments, max ~20)
        comments = PostNormalizer._extract_comments(raw_post)
        
        # Location
        location = None
        if raw_post.get('locationName'):
            location = {
                'name': raw_post['locationName'],
                'id': raw_post.get('locationId')
            }
        
        # Tagged accounts
        tagged = {
            'users': raw_post.get('taggedUsers', []),
            'coauthors': raw_post.get('coauthorProducers', [])
        }
        
        # Metadata
        metadata = {
            'is_pinned': raw_post.get('isPinned', False),
            'is_sponsored': raw_post.get('isSponsored', False),
            'is_paid_partnership': raw_post.get('paidPartnership', False),
            'sponsors': raw_post.get('sponsors', []),
            'alt_text': raw_post.get('alt'),
            'product_type': raw_post.get('productType'),  # "clips" for Reels
        }
        
        # Normalized post structure
        normalized = {
            'id': post_id,
            'type': post_type,
            'short_code': raw_post.get('shortCode', ''),
            'url': raw_post['url'],
            'timestamp': raw_post.get('timestamp', ''),
            
            'owner': owner,
            'content': content,
            'engagement': engagement,
            
            'media': {
                'images': images,
                'image_count': len(images),
                'is_video': post_type == 'Video',
                'dimensions': {
                    'height': raw_post.get('dimensionsHeight'),
                    'width': raw_post.get('dimensionsWidth')
                }
            },
            
            'comments': comments,
            'location': location,
            'tagged': tagged,
            'metadata': metadata,
            
            '_raw': raw_post  # Keep original for debugging
        }
        
        return normalized
    
    @staticmethod
    def _extract_all_images(post: Dict[str, Any]) -> List[str]:
        """
        Extract all image URLs from post
        
        For Sidecar (carousel): merges parent + all child images
        For Image/Video: just main image
        """
        images = []
        
        # Main/parent image (always present except for pure text posts)
        if post.get('displayUrl'):
            images.append(post['displayUrl'])
        
        # Additional images from images[] array (if present)
        if post.get('images'):
            for img_url in post['images']:
                if img_url and img_url not in images:
                    images.append(img_url)
        
        # Carousel children (for Sidecar type)
        if post.get('childPosts'):
            for child in post['childPosts']:
                child_url = child.get('displayUrl')
                if child_url and child_url not in images:
                    images.append(child_url)
        
        return images
    
    @staticmethod
    def _extract_comments(post: Dict[str, Any], max_comments: int = 20) -> List[Dict[str, Any]]:
        """
        Extract up to ~20 comments from post
        
        Priority:
        1. firstComment (if present and not empty)
        2. latestComments (up to remaining space)
        """
        comments = []
        
        # Add firstComment if it exists and has content
        first_comment_text = post.get('firstComment', '').strip()
        if first_comment_text:
            # Create pseudo-comment for firstComment
            # (firstComment is just text, not full comment object)
            comments.append({
                'text': first_comment_text,
                'is_first': True,
                'position': 'first'
            })
        
        # Add latestComments
        latest = post.get('latestComments', [])
        remaining_slots = max_comments - len(comments)
        
        for comment in latest[:remaining_slots]:
            normalized_comment = {
                'id': comment.get('id'),
                'text': comment.get('text', ''),
                'owner_username': comment.get('ownerUsername', ''),
                'timestamp': comment.get('timestamp'),
                'likes': comment.get('likesCount', 0),
                'replies_count': comment.get('repliesCount', 0),
                'is_first': False,
                'position': 'latest'
            }
            
            # Include comment replies if present (nested threads)
            if comment.get('replies'):
                normalized_comment['replies'] = [
                    {
                        'text': reply.get('text', ''),
                        'owner_username': reply.get('ownerUsername', ''),
                        'timestamp': reply.get('timestamp'),
                    }
                    for reply in comment['replies'][:3]  # Max 3 replies per comment
                ]
            
            comments.append(normalized_comment)
        
        return comments


class InstagramDataParser:
    """Main parser for Instagram JSON data"""
    
    def __init__(self, json_path: Path):
        self.json_path = json_path
        self.normalizer = PostNormalizer()
        self.stats = {
            'total_entries': 0,
            'valid_posts': 0,
            'error_entries': 0,
            'skipped': 0,
            'by_type': {
                'Image': 0,
                'Video': 0,
                'Sidecar': 0
            }
        }
    
    def parse(self, mode: str = 'full', sample_size: int = 50) -> List[Dict[str, Any]]:
        """
        Parse JSON and return normalized posts
        
        Args:
            mode: 'full' or 'sample'
            sample_size: number of posts if mode='sample'
        """
        logger.info(f"Parsing {self.json_path}")
        logger.info(f"Mode: {mode}" + (f" (sample_size={sample_size})" if mode == 'sample' else ""))
        
        # Load JSON
        with open(self.json_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        if not isinstance(raw_data, list):
            raise ValueError(f"Expected JSON array, got {type(raw_data)}")
        
        self.stats['total_entries'] = len(raw_data)
        logger.info(f"Total entries in file: {len(raw_data)}")
        
        # Parse all entries
        all_posts = []
        for idx, entry in enumerate(raw_data):
            if idx % 100 == 0 and idx > 0:
                logger.info(f"  Processed {idx}/{len(raw_data)} entries...")
            
            # Skip error entries
            if entry.get('error'):
                self.stats['error_entries'] += 1
                continue
            
            # Skip invalid entries (missing required fields)
            if not self._is_valid_entry(entry):
                self.stats['skipped'] += 1
                continue
            
            # Normalize and add
            try:
                normalized = self.normalizer.normalize_post(entry)
                all_posts.append(normalized)
                self.stats['valid_posts'] += 1
                self.stats['by_type'][normalized['type']] += 1
            except Exception as e:
                logger.warning(f"Error normalizing entry {idx}: {e}")
                self.stats['skipped'] += 1
        
        logger.info(f"Parsing complete. Valid posts: {len(all_posts)}")
        logger.info(f"  Image: {self.stats['by_type']['Image']}")
        logger.info(f"  Video: {self.stats['by_type']['Video']}")
        logger.info(f"  Sidecar: {self.stats['by_type']['Sidecar']}")
        
        # Sample if needed
        if mode == 'sample':
            selected = self._select_sample(all_posts, sample_size)
            logger.info(f"Selected {len(selected)} posts for sample mode")
            return selected
        
        return all_posts
    
    def _is_valid_entry(self, entry: Dict[str, Any]) -> bool:
        """Check if entry has minimum required fields"""
        required = ['id', 'url', 'ownerUsername', 'type']
        return all(field in entry for field in required)
    
    def _select_sample(self, posts: List[Dict[str, Any]], size: int) -> List[Dict[str, Any]]:
        """
        Select sample posts
        Strategy: Most recent posts
        """
        if len(posts) <= size:
            return posts
        
        # Sort by timestamp (newest first)
        sorted_posts = sorted(
            posts,
            key=lambda p: p.get('timestamp', ''),
            reverse=True
        )
        
        return sorted_posts[:size]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get parsing statistics"""
        return self.stats


# Convenience function
def parse_instagram_data(
    json_path: Path,
    mode: str = 'full',
    sample_size: int = 50
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Parse Instagram JSON data
    
    Returns:
        (posts, stats)
    """
    parser = InstagramDataParser(json_path)
    posts = parser.parse(mode=mode, sample_size=sample_size)
    stats = parser.get_stats()
    
    return posts, stats