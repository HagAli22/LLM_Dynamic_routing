"""
Automatic Response Quality Evaluation System
============================================
Evaluates LLM responses for quality, relevance, and accuracy.

Features:
- Multi-dimensional quality scoring
- Relevance detection
- Coherence analysis
- Factuality checking (basic)
- Toxicity detection
- Response completeness evaluation
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class QualityDimension(Enum):
    """Quality evaluation dimensions"""
    RELEVANCE = "relevance"
    COHERENCE = "coherence"
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    SAFETY = "safety"
    FLUENCY = "fluency"


@dataclass
class QualityScore:
    """Quality score for a response"""
    overall_score: float  # 0-100
    relevance: float
    coherence: float
    completeness: float
    accuracy: float
    safety: float
    fluency: float
    flags: List[str]
    recommendation: str  # "accept", "review", "reject"
    feedback: List[str]


class QualityEvaluator:
    """
    Automatic quality evaluation for LLM responses
    
    Uses heuristic-based methods and pattern matching to evaluate
    response quality across multiple dimensions.
    """
    
    def __init__(
        self,
        min_acceptable_score: float = 60.0,
        enable_safety_check: bool = True
    ):
        """
        Initialize quality evaluator
        
        Args:
            min_acceptable_score: Minimum score to consider acceptable
            enable_safety_check: Enable safety/toxicity checking
        """
        self.min_acceptable_score = min_acceptable_score
        self.enable_safety_check = enable_safety_check
        
        # Toxic/unsafe patterns
        self.unsafe_patterns = [
            r'\b(hate|kill|violence|harmful|dangerous)\b',
            r'\b(illegal|crime|weapon|drug)\b',
            r'\b(offensive|insulting|discriminat)\w*\b'
        ]
        
        # Incomplete response patterns
        self.incomplete_patterns = [
            r'\.{3,}$',  # Ends with ...
            r'\[.*?\]$',  # Ends with [placeholder]
            r'continue|to be continued',  # Mentions continuation
        ]
        
        # Low quality indicators
        self.low_quality_patterns = [
            r'^(i don\'t know|i cannot|i\'m not sure)',
            r'(as an ai|i am an ai)',
            r'(error|failed|unable to)',
        ]
        
        # Positive quality indicators
        self.quality_indicators = [
            r'\d+\.',  # Numbered lists
            r'[-•]\s',  # Bullet points
            r'(first|second|third|finally)',  # Structure
            r'(because|therefore|however)',  # Reasoning
        ]
    
    
    def evaluate(
        self,
        query: str,
        response: str,
        classification: Optional[str] = None,
        model: Optional[str] = None
    ) -> QualityScore:
        """
        Evaluate response quality
        
        Args:
            query: Original user query
            response: LLM response
            classification: Query classification (S/M/A)
            model: Model used
        
        Returns:
            QualityScore object
        """
        # Evaluate each dimension
        relevance = self._evaluate_relevance(query, response)
        coherence = self._evaluate_coherence(response)
        completeness = self._evaluate_completeness(response, classification)
        accuracy = self._evaluate_accuracy(query, response)
        safety = self._evaluate_safety(response) if self.enable_safety_check else 100.0
        fluency = self._evaluate_fluency(response)
        
        # Calculate overall score (weighted average)
        weights = {
            "relevance": 0.25,
            "coherence": 0.20,
            "completeness": 0.20,
            "accuracy": 0.15,
            "safety": 0.10,
            "fluency": 0.10
        }
        
        overall = (
            relevance * weights["relevance"] +
            coherence * weights["coherence"] +
            completeness * weights["completeness"] +
            accuracy * weights["accuracy"] +
            safety * weights["safety"] +
            fluency * weights["fluency"]
        )
        
        # Collect flags and feedback
        flags, feedback = self._generate_feedback(
            relevance, coherence, completeness, accuracy, safety, fluency, response
        )
        
        # Determine recommendation
        recommendation = self._get_recommendation(overall, safety, flags)
        
        return QualityScore(
            overall_score=round(overall, 2),
            relevance=round(relevance, 2),
            coherence=round(coherence, 2),
            completeness=round(completeness, 2),
            accuracy=round(accuracy, 2),
            safety=round(safety, 2),
            fluency=round(fluency, 2),
            flags=flags,
            recommendation=recommendation,
            feedback=feedback
        )
    
    
    def _evaluate_relevance(self, query: str, response: str) -> float:
        """Evaluate how relevant the response is to the query"""
        score = 70.0  # Base score
        
        # Extract keywords from query
        query_keywords = set(re.findall(r'\b\w+\b', query.lower()))
        response_lower = response.lower()
        
        # Check keyword overlap
        keyword_matches = sum(1 for kw in query_keywords if kw in response_lower)
        overlap_ratio = keyword_matches / len(query_keywords) if query_keywords else 0
        
        score += overlap_ratio * 30  # Up to 30 points for keyword overlap
        
        # Penalty for generic responses
        generic_phrases = ['i understand', 'happy to help', 'here is', 'let me']
        generic_count = sum(1 for phrase in generic_phrases if phrase in response_lower)
        if generic_count > 2:
            score -= 10
        
        # Penalty for "I don't know" type responses
        if any(pattern in response_lower for pattern in ['i don\'t know', 'i cannot answer', 'not sure']):
            score -= 30
        
        return max(0, min(100, score))
    
    
    def _evaluate_coherence(self, response: str) -> float:
        """Evaluate logical coherence and structure"""
        score = 70.0
        
        # Check sentence structure
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        # Reward well-structured responses
        if len(sentences) >= 3:
            score += 10
        
        # Check for transition words (indicates flow)
        transitions = ['however', 'therefore', 'additionally', 'furthermore', 'moreover']
        transition_count = sum(1 for word in transitions if word in response.lower())
        score += min(transition_count * 5, 15)
        
        # Check for lists/structure
        if re.search(r'\d+\.|\-|\•', response):
            score += 10
        
        # Penalty for repetition
        words = response.lower().split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.5:  # High repetition
                score -= 20
        
        return max(0, min(100, score))
    
    
    def _evaluate_completeness(self, response: str, classification: Optional[str]) -> float:
        """Evaluate if response is complete"""
        score = 80.0
        
        # Check length based on classification
        word_count = len(response.split())
        
        if classification == "S":  # Simple queries
            if word_count < 10:
                score -= 30
            elif word_count < 20:
                score -= 10
        elif classification == "M":  # Medium queries
            if word_count < 30:
                score -= 30
            elif word_count < 50:
                score -= 15
        elif classification == "A":  # Advanced queries
            if word_count < 50:
                score -= 40
            elif word_count < 100:
                score -= 20
        
        # Check for incomplete patterns
        for pattern in self.incomplete_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                score -= 25
                break
        
        # Check if response ends properly
        if response and response[-1] not in '.!?':
            score -= 10
        
        return max(0, min(100, score))
    
    
    def _evaluate_accuracy(self, query: str, response: str) -> float:
        """
        Evaluate potential accuracy (basic heuristics)
        Note: Full accuracy checking requires fact-checking APIs
        """
        score = 75.0  # Neutral baseline
        
        # Check for hedging language (indicates uncertainty)
        hedging_phrases = ['might be', 'could be', 'possibly', 'perhaps', 'i think']
        hedging_count = sum(1 for phrase in hedging_phrases if phrase in response.lower())
        
        if hedging_count > 3:
            score -= 15
        elif hedging_count > 1:
            score -= 5
        
        # Check for confidence indicators
        confidence_phrases = ['is', 'are', 'specifically', 'exactly', 'definitely']
        confidence_count = sum(1 for phrase in confidence_phrases if phrase in response.lower())
        
        if confidence_count > 5:
            score += 10
        
        # Penalty for contradictions
        contradiction_patterns = [
            (r'\byes\b.*\bno\b', r'\bno\b.*\byes\b'),
            (r'\btrue\b.*\bfalse\b', r'\bfalse\b.*\btrue\b'),
        ]
        
        for pattern1, pattern2 in contradiction_patterns:
            if re.search(pattern1, response.lower()) or re.search(pattern2, response.lower()):
                score -= 20
                break
        
        # Check for sources/citations (positive indicator)
        if re.search(r'(according to|source|research|study)', response.lower()):
            score += 10
        
        return max(0, min(100, score))
    
    
    def _evaluate_safety(self, response: str) -> float:
        """Evaluate safety and detect toxic content"""
        score = 100.0
        
        response_lower = response.lower()
        
        # Check for unsafe patterns
        for pattern in self.unsafe_patterns:
            if re.search(pattern, response_lower):
                score -= 30
        
        # Check for personal information leakage
        pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        ]
        
        for pattern in pii_patterns:
            if re.search(pattern, response):
                score -= 40
        
        # Check for inappropriate content
        inappropriate = ['nsfw', 'explicit', 'graphic']
        if any(word in response_lower for word in inappropriate):
            score -= 50
        
        return max(0, min(100, score))
    
    
    def _evaluate_fluency(self, response: str) -> float:
        """Evaluate language fluency and readability"""
        score = 80.0
        
        # Check for proper capitalization
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if sentences:
            # Check if sentences start with capital letters
            capitalized = sum(1 for s in sentences if s and s[0].isupper())
            cap_ratio = capitalized / len(sentences)
            score += (cap_ratio - 0.8) * 50  # Expect 80%+ capitalized
        
        # Check for excessive punctuation
        punct_count = sum(1 for c in response if c in '!?.')
        word_count = len(response.split())
        if word_count > 0:
            punct_ratio = punct_count / word_count
            if punct_ratio > 0.3:  # Too much punctuation
                score -= 15
        
        # Check for spelling indicators (repeated characters)
        if re.search(r'(.)\1{3,}', response):  # Like "hellooooo"
            score -= 20
        
        # Check for proper spacing
        if re.search(r'\w{50,}', response):  # Very long word (likely error)
            score -= 15
        
        return max(0, min(100, score))
    
    
    def _generate_feedback(
        self,
        relevance: float,
        coherence: float,
        completeness: float,
        accuracy: float,
        safety: float,
        fluency: float,
        response: str
    ) -> Tuple[List[str], List[str]]:
        """Generate flags and feedback"""
        flags = []
        feedback = []
        
        # Low scores
        if relevance < 50:
            flags.append("low_relevance")
            feedback.append("Response may not be relevant to the query")
        
        if coherence < 50:
            flags.append("low_coherence")
            feedback.append("Response lacks logical structure")
        
        if completeness < 50:
            flags.append("incomplete")
            feedback.append("Response appears incomplete")
        
        if accuracy < 50:
            flags.append("low_confidence")
            feedback.append("Response may contain uncertain information")
        
        if safety < 80:
            flags.append("safety_concern")
            feedback.append("Response may contain unsafe content")
        
        if fluency < 50:
            flags.append("low_fluency")
            feedback.append("Response has fluency issues")
        
        # Positive feedback
        if relevance > 85 and coherence > 85:
            feedback.append("High quality response with good structure")
        
        # Length check
        word_count = len(response.split())
        if word_count < 10:
            flags.append("too_short")
            feedback.append("Response is very short")
        elif word_count > 500:
            flags.append("very_long")
            feedback.append("Response is very long")
        
        return flags, feedback
    
    
    def _get_recommendation(
        self,
        overall: float,
        safety: float,
        flags: List[str]
    ) -> str:
        """Get recommendation based on scores"""
        # Safety is critical
        if safety < 80:
            return "reject"
        
        # Check for critical flags
        critical_flags = ["safety_concern", "incomplete", "low_relevance"]
        if any(flag in flags for flag in critical_flags):
            if overall < 60:
                return "reject"
            else:
                return "review"
        
        # Based on overall score
        if overall >= self.min_acceptable_score:
            return "accept"
        elif overall >= 40:
            return "review"
        else:
            return "reject"
    
    
    def batch_evaluate(
        self,
        queries: List[str],
        responses: List[str],
        classifications: Optional[List[str]] = None
    ) -> List[QualityScore]:
        """Evaluate multiple responses in batch"""
        classifications = classifications or [None] * len(queries)
        
        results = []
        for query, response, classification in zip(queries, responses, classifications):
            score = self.evaluate(query, response, classification)
            results.append(score)
        
        return results
    
    
    def get_statistics(self, scores: List[QualityScore]) -> Dict:
        """Get statistics from multiple quality scores"""
        if not scores:
            return {}
        
        return {
            "total_evaluated": len(scores),
            "avg_overall_score": sum(s.overall_score for s in scores) / len(scores),
            "avg_relevance": sum(s.relevance for s in scores) / len(scores),
            "avg_coherence": sum(s.coherence for s in scores) / len(scores),
            "avg_completeness": sum(s.completeness for s in scores) / len(scores),
            "recommendations": {
                "accept": sum(1 for s in scores if s.recommendation == "accept"),
                "review": sum(1 for s in scores if s.recommendation == "review"),
                "reject": sum(1 for s in scores if s.recommendation == "reject")
            },
            "common_flags": self._get_common_flags(scores)
        }
    
    
    def _get_common_flags(self, scores: List[QualityScore]) -> Dict[str, int]:
        """Get most common flags"""
        flag_counts = {}
        for score in scores:
            for flag in score.flags:
                flag_counts[flag] = flag_counts.get(flag, 0) + 1
        return dict(sorted(flag_counts.items(), key=lambda x: x[1], reverse=True))
