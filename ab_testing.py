"""
A/B Testing Framework for LLM Models
====================================
Enables controlled experiments to compare model performance.

Features:
- Multi-variant testing
- Traffic splitting
- Statistical significance testing
- Performance comparison
- Automated winner selection
"""

import time
import random
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
from datetime import datetime
import statistics
from pathlib import Path


@dataclass
class Variant:
    """A/B test variant configuration"""
    name: str
    model: str
    traffic_percentage: float  # 0-100
    description: str


@dataclass
class VariantMetrics:
    """Metrics for a test variant"""
    variant_name: str
    total_queries: int
    successful_queries: int
    failed_queries: int
    avg_response_time: float
    avg_cost: float
    avg_quality_score: float
    user_satisfaction: float  # 0-5 scale
    conversion_rate: float  # If applicable


@dataclass
class ABTestResult:
    """Results of an A/B test"""
    test_id: str
    test_name: str
    start_time: float
    end_time: Optional[float]
    status: str  # running, completed, stopped
    variants: List[Variant]
    metrics: Dict[str, VariantMetrics]
    winner: Optional[str]
    confidence: float  # 0-100
    statistical_significance: bool
    recommendation: str


class ABTest:
    """
    Individual A/B test
    """
    
    def __init__(
        self,
        test_id: str,
        test_name: str,
        variants: List[Variant],
        duration: Optional[int] = None,
        min_samples: int = 100
    ):
        """
        Initialize A/B test
        
        Args:
            test_id: Unique test identifier
            test_name: Descriptive test name
            variants: List of variants to test
            duration: Test duration in seconds (None = unlimited)
            min_samples: Minimum samples per variant before declaring winner
        """
        self.test_id = test_id
        self.test_name = test_name
        self.variants = variants
        self.duration = duration
        self.min_samples = min_samples
        
        # Validate traffic percentages
        total_traffic = sum(v.traffic_percentage for v in variants)
        if abs(total_traffic - 100.0) > 0.01:
            raise ValueError(f"Traffic percentages must sum to 100, got {total_traffic}")
        
        self.start_time = time.time()
        self.end_time = None
        self.status = "running"
        
        # Metrics storage
        self.query_data: Dict[str, List[Dict]] = defaultdict(list)
        self.variant_metrics: Dict[str, VariantMetrics] = {}
        
        self.winner = None
        self.confidence = 0.0
    
    
    def assign_variant(self, user_id: Optional[str] = None) -> str:
        """
        Assign a variant to a request
        
        Args:
            user_id: Optional user ID for consistent assignment
        
        Returns:
            Variant name
        """
        if user_id:
            # Consistent assignment for same user
            random.seed(hash(user_id))
        
        rand = random.random() * 100
        cumulative = 0
        
        for variant in self.variants:
            cumulative += variant.traffic_percentage
            if rand <= cumulative:
                if user_id:
                    random.seed()  # Reset seed
                return variant.name
        
        # Fallback
        if user_id:
            random.seed()
        return self.variants[0].name
    
    
    def record_result(
        self,
        variant_name: str,
        success: bool,
        response_time: float,
        cost: float,
        quality_score: Optional[float] = None,
        user_satisfaction: Optional[float] = None,
        converted: bool = False
    ):
        """Record a result for a variant"""
        self.query_data[variant_name].append({
            "timestamp": time.time(),
            "success": success,
            "response_time": response_time,
            "cost": cost,
            "quality_score": quality_score,
            "user_satisfaction": user_satisfaction,
            "converted": converted
        })
    
    
    def get_variant_model(self, variant_name: str) -> Optional[str]:
        """Get model for a variant"""
        for variant in self.variants:
            if variant.name == variant_name:
                return variant.model
        return None
    
    
    def calculate_metrics(self):
        """Calculate metrics for all variants"""
        for variant in self.variants:
            data = self.query_data[variant.name]
            
            if not data:
                continue
            
            total = len(data)
            successful = sum(1 for d in data if d["success"])
            failed = total - successful
            
            response_times = [d["response_time"] for d in data]
            costs = [d["cost"] for d in data]
            quality_scores = [d["quality_score"] for d in data if d["quality_score"] is not None]
            satisfactions = [d["user_satisfaction"] for d in data if d["user_satisfaction"] is not None]
            conversions = sum(1 for d in data if d["converted"])
            
            self.variant_metrics[variant.name] = VariantMetrics(
                variant_name=variant.name,
                total_queries=total,
                successful_queries=successful,
                failed_queries=failed,
                avg_response_time=statistics.mean(response_times) if response_times else 0.0,
                avg_cost=statistics.mean(costs) if costs else 0.0,
                avg_quality_score=statistics.mean(quality_scores) if quality_scores else 0.0,
                user_satisfaction=statistics.mean(satisfactions) if satisfactions else 0.0,
                conversion_rate=conversions / total if total > 0 else 0.0
            )
    
    
    def determine_winner(self, primary_metric: str = "avg_quality_score") -> Tuple[Optional[str], float]:
        """
        Determine test winner based on primary metric
        
        Args:
            primary_metric: Metric to optimize for
        
        Returns:
            Tuple of (winner_name, confidence)
        """
        self.calculate_metrics()
        
        # Check if we have enough samples
        for variant in self.variants:
            if len(self.query_data[variant.name]) < self.min_samples:
                return None, 0.0
        
        # Get metric values
        metric_values = {}
        for variant_name, metrics in self.variant_metrics.items():
            metric_values[variant_name] = getattr(metrics, primary_metric, 0)
        
        if not metric_values:
            return None, 0.0
        
        # Find best variant
        if primary_metric in ["avg_response_time", "avg_cost", "failed_queries"]:
            # Lower is better
            winner = min(metric_values, key=metric_values.get)
        else:
            # Higher is better
            winner = max(metric_values, key=metric_values.get)
        
        # Calculate confidence using simple statistical test
        confidence = self._calculate_confidence(winner, metric_values, primary_metric)
        
        self.winner = winner
        self.confidence = confidence
        
        return winner, confidence
    
    
    def _calculate_confidence(
        self,
        winner: str,
        metric_values: Dict[str, float],
        primary_metric: str
    ) -> float:
        """
        Calculate confidence in winner (simplified statistical test)
        
        In production, use proper statistical tests like t-test or chi-squared
        """
        winner_value = metric_values[winner]
        other_values = [v for k, v in metric_values.items() if k != winner]
        
        if not other_values:
            return 100.0
        
        avg_other = statistics.mean(other_values)
        
        # Calculate relative difference
        if avg_other == 0:
            return 100.0
        
        if primary_metric in ["avg_response_time", "avg_cost"]:
            # Lower is better
            improvement = (avg_other - winner_value) / avg_other
        else:
            # Higher is better
            improvement = (winner_value - avg_other) / avg_other if avg_other != 0 else 0
        
        # Convert improvement to confidence (simplified)
        # In production, use proper statistical significance testing
        confidence = min(100, max(0, improvement * 100 + 50))
        
        return round(confidence, 2)
    
    
    def is_complete(self) -> bool:
        """Check if test is complete"""
        if self.status != "running":
            return True
        
        # Check duration
        if self.duration and (time.time() - self.start_time) >= self.duration:
            return True
        
        # Check if we have enough data
        for variant in self.variants:
            if len(self.query_data[variant.name]) < self.min_samples:
                return False
        
        return True
    
    
    def stop(self):
        """Stop the test"""
        self.status = "stopped"
        self.end_time = time.time()
    
    
    def complete(self):
        """Mark test as complete"""
        self.status = "completed"
        self.end_time = time.time()


class ABTestingFramework:
    """
    Framework for managing multiple A/B tests
    """
    
    def __init__(self, results_dir: str = "ab_tests"):
        """Initialize A/B testing framework"""
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        self.active_tests: Dict[str, ABTest] = {}
        self.completed_tests: List[ABTestResult] = []
        
        # Load existing tests
        self._load_tests()
    
    
    def create_test(
        self,
        test_name: str,
        variants: List[Variant],
        duration: Optional[int] = None,
        min_samples: int = 100
    ) -> str:
        """
        Create a new A/B test
        
        Returns:
            Test ID
        """
        test_id = f"test_{int(time.time())}_{hash(test_name) % 10000}"
        
        test = ABTest(
            test_id=test_id,
            test_name=test_name,
            variants=variants,
            duration=duration,
            min_samples=min_samples
        )
        
        self.active_tests[test_id] = test
        
        print(f"✅ A/B Test '{test_name}' created with ID: {test_id}")
        print(f"   Variants: {', '.join(v.name for v in variants)}")
        print(f"   Duration: {duration}s" if duration else "   Duration: Unlimited")
        
        return test_id
    
    
    def get_variant_for_request(
        self,
        test_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Tuple[str, str]]:
        """
        Get variant assignment for a request
        
        Returns:
            Tuple of (variant_name, model) or None if test not found
        """
        if test_id not in self.active_tests:
            return None
        
        test = self.active_tests[test_id]
        variant_name = test.assign_variant(user_id)
        model = test.get_variant_model(variant_name)
        
        return variant_name, model
    
    
    def record_result(self, test_id: str, variant_name: str, **kwargs):
        """Record result for a test variant"""
        if test_id in self.active_tests:
            self.active_tests[test_id].record_result(variant_name, **kwargs)
    
    
    def check_tests(self):
        """Check all active tests and complete finished ones"""
        completed_ids = []
        
        for test_id, test in self.active_tests.items():
            if test.is_complete():
                test.complete()
                winner, confidence = test.determine_winner()
                
                # Create result
                result = ABTestResult(
                    test_id=test.test_id,
                    test_name=test.test_name,
                    start_time=test.start_time,
                    end_time=test.end_time,
                    status=test.status,
                    variants=test.variants,
                    metrics=test.variant_metrics,
                    winner=winner,
                    confidence=confidence,
                    statistical_significance=confidence > 95,
                    recommendation=self._get_recommendation(winner, confidence)
                )
                
                self.completed_tests.append(result)
                completed_ids.append(test_id)
                
                # Save result
                self._save_test_result(result)
                
                print(f"✅ A/B Test '{test.test_name}' completed!")
                print(f"   Winner: {winner} (Confidence: {confidence:.2f}%)")
        
        # Remove completed tests from active
        for test_id in completed_ids:
            del self.active_tests[test_id]
    
    
    def get_test_status(self, test_id: str) -> Optional[Dict]:
        """Get status of a test"""
        if test_id in self.active_tests:
            test = self.active_tests[test_id]
            test.calculate_metrics()
            
            return {
                "test_id": test.test_id,
                "test_name": test.test_name,
                "status": test.status,
                "runtime": time.time() - test.start_time,
                "variants": [asdict(v) for v in test.variants],
                "metrics": {k: asdict(v) for k, v in test.variant_metrics.items()},
                "winner": test.winner,
                "confidence": test.confidence
            }
        
        return None
    
    
    def get_all_active_tests(self) -> List[Dict]:
        """Get all active tests"""
        return [self.get_test_status(test_id) for test_id in self.active_tests.keys()]
    
    
    def stop_test(self, test_id: str):
        """Stop a test manually"""
        if test_id in self.active_tests:
            self.active_tests[test_id].stop()
            self.check_tests()
    
    
    def _get_recommendation(self, winner: Optional[str], confidence: float) -> str:
        """Get recommendation based on test results"""
        if not winner:
            return "Insufficient data - continue testing"
        
        if confidence > 95:
            return f"Deploy {winner} - High confidence"
        elif confidence > 80:
            return f"Consider deploying {winner} - Moderate confidence"
        else:
            return "Continue testing - Low confidence"
    
    
    def _save_test_result(self, result: ABTestResult):
        """Save test result to file"""
        filename = self.results_dir / f"{result.test_id}.json"
        
        result_dict = asdict(result)
        # Convert metrics to dict
        result_dict["metrics"] = {k: asdict(v) for k, v in result.metrics.items()}
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
    
    
    def _load_tests(self):
        """Load completed tests from disk"""
        if not self.results_dir.exists():
            return
        
        for filepath in self.results_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Note: Proper deserialization would reconstruct ABTestResult
                    # For now, just store the dict
                    # self.completed_tests.append(data)
            except Exception as e:
                print(f"Warning: Failed to load test result {filepath}: {e}")
    
    
    def generate_report(self, test_id: Optional[str] = None) -> str:
        """Generate a report for a test or all tests"""
        if test_id:
            status = self.get_test_status(test_id)
            if not status:
                return "Test not found"
            
            report = f"\n{'='*70}\n"
            report += f"A/B TEST REPORT: {status['test_name']}\n"
            report += f"{'='*70}\n\n"
            report += f"Test ID: {status['test_id']}\n"
            report += f"Status: {status['status']}\n"
            report += f"Runtime: {status['runtime']:.0f}s\n\n"
            
            report += "VARIANTS:\n"
            for variant in status['variants']:
                report += f"  • {variant['name']}: {variant['model']} ({variant['traffic_percentage']}%)\n"
            
            report += "\nMETRICS:\n"
            for variant_name, metrics in status['metrics'].items():
                report += f"\n  {variant_name}:\n"
                report += f"    Total Queries: {metrics['total_queries']}\n"
                report += f"    Success Rate: {metrics['successful_queries'] / metrics['total_queries'] * 100:.1f}%\n"
                report += f"    Avg Response Time: {metrics['avg_response_time']:.2f}s\n"
                report += f"    Avg Cost: ${metrics['avg_cost']:.4f}\n"
                report += f"    Avg Quality Score: {metrics['avg_quality_score']:.2f}\n"
            
            if status['winner']:
                report += f"\n🏆 WINNER: {status['winner']} (Confidence: {status['confidence']:.2f}%)\n"
            
            report += f"\n{'='*70}\n"
            return report
        
        else:
            # Generate report for all active tests
            report = f"\n{'='*70}\n"
            report += f"ALL ACTIVE A/B TESTS\n"
            report += f"{'='*70}\n\n"
            
            for test_id in self.active_tests.keys():
                status = self.get_test_status(test_id)
                report += f"• {status['test_name']} ({test_id})\n"
                report += f"  Status: {status['status']} | Runtime: {status['runtime']:.0f}s\n"
                if status['winner']:
                    report += f"  Winner: {status['winner']} ({status['confidence']:.1f}%)\n"
                report += "\n"
            
            return report
