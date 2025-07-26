"""
Smart content-aware chunker with optimized chunk sizes for different content types
"""
import re
import os
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from src.config.settings import get_settings


@dataclass
class DocumentChunk:
    text: str
    metadata: Dict[str, Any]
    chunk_id: str
    page_number: int = None
    content_type: str = "general"


class SmartContentChunker:
    """Smart chunker with content-aware algorithms and optimized chunk sizes"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Content-specific chunk sizes (optimized for each type)
        self.chunk_sizes = {
            'mcq': 800,        # Single MCQ with options
            'creative': 1500,   # Creative questions with context
            'table': 1200,      # Table rows with structure
            'general': 1000,    # General text content
            'raw': 1000        # Raw OCR content
        }
        
        # Content-specific overlap
        self.overlaps = {
            'mcq': 50,         # Minimal overlap for discrete questions
            'creative': 150,    # More overlap for context preservation
            'table': 100,       # Medium overlap for table continuity
            'general': 100,     # Standard overlap
            'raw': 100         # Standard overlap
        }
    
    def chunk_separated_content_only(self, base_path: str) -> List[DocumentChunk]:
        """
        Process only the separated content files with smart chunking
        
        Args:
            base_path: Base path to processed documents
            
        Returns:
            List of optimally chunked documents
        """
        all_chunks = []
        
        # Process only separated content files
        content_files = {
            'mcq_content.txt': 'mcq',
            'creative_questions.txt': 'creative', 
            'table_content.txt': 'table',
            'rest_content.txt': 'general'
        }
        
        separated_path = os.path.join(base_path, 'separated_content')
        
        for filename, content_type in content_files.items():
            file_path = os.path.join(separated_path, filename)
            
            if os.path.exists(file_path):
                chunks = self._chunk_by_content_type(file_path, content_type)
                all_chunks.extend(chunks)
                print(f"✅ {filename}: {len(chunks)} chunks (avg size: {self._avg_chunk_size(chunks):.0f} chars)")
        
        print(f"🎯 Total chunks created: {len(all_chunks)}")
        return all_chunks
    
    def _chunk_by_content_type(self, file_path: str, content_type: str) -> List[DocumentChunk]:
        """Smart chunking based on content type"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content_type == 'mcq':
            return self._chunk_mcq_smart(content, file_path)
        elif content_type == 'creative':
            return self._chunk_creative_smart(content, file_path)
        elif content_type == 'table':
            return self._chunk_table_smart(content, file_path)
        else:
            return self._chunk_general_smart(content, file_path, content_type)
    
    def _chunk_mcq_smart(self, content: str, file_path: str) -> List[DocumentChunk]:
        """
        Smart MCQ chunking - each question as a separate chunk
        Separated by newlines as you mentioned
        """
        chunks = []
        
        # Split by double newlines or question patterns
        questions = re.split(r'\n\n+|(?=\d+[\।.])', content)
        
        for i, question_block in enumerate(questions):
            question_block = question_block.strip()
            if not question_block or len(question_block) < 30:
                continue
            
            # Clean the question
            clean_question = self._clean_text(question_block)
            
            chunk = DocumentChunk(
                text=clean_question,
                chunk_id=f"mcq_{i}_{hash(clean_question) % 10000}",
                metadata={
                    'content_type': 'mcq',
                    'source_file': file_path,
                    'chunk_index': i,
                    'question_number': self._extract_question_number(clean_question)
                },
                content_type="mcq"
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_creative_smart(self, content: str, file_path: str) -> List[DocumentChunk]:
        """
        Smart creative question chunking - separated by --- as you mentioned
        Each question with its context and sub-questions
        """
        chunks = []
        
        # Split by --- separators
        question_sections = content.split('---')
        
        for i, section in enumerate(question_sections):
            section = section.strip()
            if not section or len(section) < 50:
                continue
            
            # Each creative question section is already well-sized
            # No need to split further as they contain context + questions
            
            chunk = DocumentChunk(
                text=section,
                chunk_id=f"creative_{i}_{hash(section) % 10000}",
                metadata={
                    'content_type': 'creative',
                    'source_file': file_path,
                    'chunk_index': i,
                    'question_set': f"Question {i + 1}"
                },
                content_type="creative"
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_table_smart(self, content: str, file_path: str) -> List[DocumentChunk]:
        """
        Smart table chunking - separated by newlines as you mentioned
        Preserve table structure
        """
        chunks = []
        
        # Split by double newlines to get table sections
        table_sections = re.split(r'\n\n+', content)
        
        chunk_size = self.chunk_sizes['table']
        overlap = self.overlaps['table']
        
        for section_idx, section in enumerate(table_sections):
            section = section.strip()
            if not section:
                continue
            
            if len(section) <= chunk_size:
                # Section fits in one chunk
                chunk = DocumentChunk(
                    text=section,
                    chunk_id=f"table_{section_idx}_{hash(section) % 10000}",
                    metadata={
                        'content_type': 'table',
                        'source_file': file_path,
                        'chunk_index': section_idx,
                        'table_section': section_idx + 1
                    },
                    content_type="table"
                )
                chunks.append(chunk)
            else:
                # Split large table section by rows
                rows = section.split('\n')
                current_chunk = ""
                sub_chunk_idx = 0
                
                for row in rows:
                    if len(current_chunk) + len(row) + 1 <= chunk_size:
                        current_chunk += row + "\n"
                    else:
                        if current_chunk.strip():
                            chunk = DocumentChunk(
                                text=current_chunk.strip(),
                                chunk_id=f"table_{section_idx}_{sub_chunk_idx}_{hash(current_chunk) % 10000}",
                                metadata={
                                    'content_type': 'table',
                                    'source_file': file_path,
                                    'chunk_index': f"{section_idx}.{sub_chunk_idx}",
                                    'table_section': section_idx + 1
                                },
                                content_type="table"
                            )
                            chunks.append(chunk)
                            sub_chunk_idx += 1
                        
                        # Start new chunk with overlap
                        overlap_rows = current_chunk.split('\n')[-2:] if overlap > 0 else []
                        current_chunk = '\n'.join(overlap_rows) + '\n' + row + '\n'
                
                # Add final chunk
                if current_chunk.strip():
                    chunk = DocumentChunk(
                        text=current_chunk.strip(),
                        chunk_id=f"table_{section_idx}_{sub_chunk_idx}_{hash(current_chunk) % 10000}",
                        metadata={
                            'content_type': 'table',
                            'source_file': file_path,
                            'chunk_index': f"{section_idx}.{sub_chunk_idx}",
                            'table_section': section_idx + 1
                        },
                        content_type="table"
                    )
                    chunks.append(chunk)
        
        return chunks
    
    def _chunk_general_smart(self, content: str, file_path: str, content_type: str) -> List[DocumentChunk]:
        """Smart general content chunking with sentence awareness"""
        chunks = []
        
        chunk_size = self.chunk_sizes[content_type]
        overlap = self.overlaps[content_type]
        
        # Split by sentences for better chunking
        sentences = self._split_sentences_smart(content)
        
        current_chunk = ""
        chunk_idx = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    chunk = DocumentChunk(
                        text=current_chunk.strip(),
                        chunk_id=f"{content_type}_{chunk_idx}_{hash(current_chunk) % 10000}",
                        metadata={
                            'content_type': content_type,
                            'source_file': file_path,
                            'chunk_index': chunk_idx
                        },
                        content_type=content_type
                    )
                    chunks.append(chunk)
                    chunk_idx += 1
                
                # Add overlap
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else ""
                current_chunk = overlap_text + sentence + " "
        
        # Add final chunk
        if current_chunk.strip():
            chunk = DocumentChunk(
                text=current_chunk.strip(),
                chunk_id=f"{content_type}_{chunk_idx}_{hash(current_chunk) % 10000}",
                metadata={
                    'content_type': content_type,
                    'source_file': file_path,
                    'chunk_index': chunk_idx
                },
                content_type=content_type
            )
            chunks.append(chunk)
        
        return chunks
    
    def _extract_question_number(self, text: str) -> str:
        """Extract question number from MCQ text"""
        match = re.match(r'(\d+)', text.strip())
        return match.group(1) if match else "unknown"
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove markdown-style markers
        text = re.sub(r'\*\*.*?\*\*', '', text)
        text = re.sub(r'📖|🎯|✓', '', text)
        return text.strip()
    
    def _split_sentences_smart(self, text: str) -> List[str]:
        """Smart sentence splitting for Bengali text"""
        # Bengali sentence endings and paragraph breaks
        sentence_pattern = r'[।৺]|\n\n+'
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _avg_chunk_size(self, chunks: List[DocumentChunk]) -> float:
        """Calculate average chunk size"""
        if not chunks:
            return 0
        return sum(len(chunk.text) for chunk in chunks) / len(chunks)
    
    def get_chunking_stats(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """Get detailed chunking statistics"""
        stats = {
            'total_chunks': len(chunks),
            'by_content_type': {},
            'avg_chunk_size': self._avg_chunk_size(chunks),
            'chunk_size_ranges': {}
        }
        
        # Group by content type
        for chunk in chunks:
            content_type = chunk.content_type
            if content_type not in stats['by_content_type']:
                stats['by_content_type'][content_type] = {
                    'count': 0,
                    'avg_size': 0,
                    'min_size': float('inf'),
                    'max_size': 0
                }
            
            stats['by_content_type'][content_type]['count'] += 1
            chunk_len = len(chunk.text)
            stats['by_content_type'][content_type]['min_size'] = min(
                stats['by_content_type'][content_type]['min_size'], chunk_len
            )
            stats['by_content_type'][content_type]['max_size'] = max(
                stats['by_content_type'][content_type]['max_size'], chunk_len
            )
        
        # Calculate averages
        for content_type, data in stats['by_content_type'].items():
            type_chunks = [c for c in chunks if c.content_type == content_type]
            data['avg_size'] = sum(len(c.text) for c in type_chunks) / len(type_chunks)
        
        return stats
