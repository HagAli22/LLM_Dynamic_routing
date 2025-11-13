"""
Advanced Monitoring and Metrics System for LLM Router
=====================================================
Provides comprehensive monitoring, metrics collection, and analytics.

Features:
- Real-time performance metrics
- Query analytics and trends
- Cost tracking and optimization
- Model performance comparison
- Anomaly detection
- Custom alerts
"""

import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
from pathlib import Path
import threading


@dataclass
class QueryMetrics:
    """Metrics for a single query"""
    query_id: str
    timestamp: float
    query_text: str
    classification: str
    tier: str
    model_used: str
    cache_hit: bool
    processing_time: float
    success: bool
    error: Optional[str]
    tokens_used: Optional[int]
    cost: Optional[float]
    response_length: int
    user_id: Optional[str]
    session_id: Optional[str]


@dataclass
class AggregatedMetrics:
    """Aggregated metrics over a time period"""
    total_queries: int
    successful_queries: int
    failed_queries: int
    success_rate: float
    cache_hit_rate: float
    avg_processing_time: float
    median_processing_time: float
    p95_processing_time: float
    p99_processing_time: float
    total_cost: float
    avg_cost_per_query: float
    queries_by_tier: Dict[str, int]
    queries_by_classification: Dict[str, int]
    queries_by_model: Dict[str, int]
    error_rate: float
    total_tokens: int


@dataclass
class ModelPerformance:
    """Performance metrics for a specific model"""
    model_name: str
    total_queries: int
    success_rate: float
    avg_response_time: float
    avg_cost: float
    error_count: int
    last_used: float


class AdvancedMonitoring:
    """
    Advanced monitoring system for LLM Router
    
    Features:
    - Real-time metrics collection
    - Time-series data storage
    - Performance analytics
    - Anomaly detection
    - Custom alerts
    """
    
    def __init__(
        self,
        metrics_file: str = "metrics/query_metrics.jsonl",
        window_size: int = 1000,
        enable_alerts: bool = True,
        alert_thresholds: Optional[Dict] = None
    ):
        """
        Initialize monitoring system
        
        Args:
            metrics_file: Path to store metrics data
            window_size: Number of recent queries to keep in memory
            enable_alerts: Enable alert system
            alert_thresholds: Custom alert thresholds
        """
        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(exist_ok=True)
        
        self.window_size = window_size
        self.enable_alerts = enable_alerts
        
        # Default alert thresholds
        self.alert_thresholds = {
            "error_rate": 0.1,  # 10%
            "avg_processing_time": 10.0,  # 10 seconds
            "p95_processing_time": 15.0,  # 15 seconds
            "cost_per_query": 0.05,  # $0.05
        }
        if alert_thresholds:
            self.alert_thresholds.update(alert_thresholds)
        
        # In-memory storage for recent queries
        self.recent_queries: deque = deque(maxlen=window_size)
        
        # Aggregated statistics
        self.stats = defaultdict(lambda: defaultdict(int))
        
        # Model performance tracking
        self.model_performance: Dict[str, List[float]] = defaultdict(list)
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        # Alert history
        self.alert_history: List[Dict] = []
    
    
    def record_query(
        self,
        query_id: str,
        query_text: str,
        classification: str,
        tier: str,
        model_used: str,
        cache_hit: bool,
        processing_time: float,
        success: bool,
        error: Optional[str] = None,
        tokens_used: Optional[int] = None,
        cost: Optional[float] = None,
        response_length: int = 0,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Record metrics for a query"""
        metrics = QueryMetrics(
            query_id=query_id,
            timestamp=time.time(),
            query_text=query_text[:100],  # Truncate for storage
            classification=classification,
            tier=tier,
            model_used=model_used,
            cache_hit=cache_hit,
            processing_time=processing_time,
            success=success,
            error=error,
            tokens_used=tokens_used,
            cost=cost or 0.0,
            response_length=response_length,
            user_id=user_id,
            session_id=session_id
        )
        
        with self._lock:
            # Add to recent queries
            self.recent_queries.append(metrics)
            
            # Update stats
            self._update_stats(metrics)
            
            # Save to disk
            self._save_metrics(metrics)
            
            # Check for alerts
            if self.enable_alerts:
                self._check_alerts()
    
    
    def _update_stats(self, metrics: QueryMetrics):
        """Update aggregated statistics"""
        self.stats["total"]["queries"] += 1
        
        if metrics.success:
            self.stats["total"]["successful"] += 1
        else:
            self.stats["total"]["failed"] += 1
        
        if metrics.cache_hit:
            self.stats["total"]["cache_hits"] += 1
        
        self.stats["by_tier"][metrics.tier] += 1
        self.stats["by_classification"][metrics.classification] += 1
        self.stats["by_model"][metrics.model_used] += 1
        
        self.stats["total"]["processing_time"] += metrics.processing_time
        self.stats["total"]["cost"] += metrics.cost or 0.0
        self.stats["total"]["tokens"] += metrics.tokens_used or 0
        
        # Track model performance
        self.model_performance[metrics.model_used].append(metrics.processing_time)
    
    
    def _save_metrics(self, metrics: QueryMetrics):
        """Save metrics to disk (JSONL format)"""
        try:
            with open(self.metrics_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(metrics)) + "\n")
        except Exception as e:
            print(f"Warning: Failed to save metrics: {e}")
    
    
    def get_aggregated_metrics(
        self,
        time_window: Optional[int] = None
    ) -> AggregatedMetrics:
        """
        Get aggregated metrics
        
        Args:
            time_window: Time window in seconds (None = all recent queries)
        
        Returns:
            AggregatedMetrics object
        """
        with self._lock:
            # Filter queries by time window if specified
            if time_window:
                cutoff = time.time() - time_window
                queries = [q for q in self.recent_queries if q.timestamp >= cutoff]
            else:
                queries = list(self.recent_queries)
            
            if not queries:
                return self._empty_metrics()
            
            # Calculate metrics
            total = len(queries)
            successful = sum(1 for q in queries if q.success)
            failed = total - successful
            cache_hits = sum(1 for q in queries if q.cache_hit)
            
            processing_times = [q.processing_time for q in queries]
            costs = [q.cost or 0.0 for q in queries]
            
            queries_by_tier = defaultdict(int)
            queries_by_classification = defaultdict(int)
            queries_by_model = defaultdict(int)
            
            for q in queries:
                queries_by_tier[q.tier] += 1
                queries_by_classification[q.classification] += 1
                queries_by_model[q.model_used] += 1
            
            return AggregatedMetrics(
                total_queries=total,
                successful_queries=successful,
                failed_queries=failed,
                success_rate=successful / total if total > 0 else 0.0,
                cache_hit_rate=cache_hits / total if total > 0 else 0.0,
                avg_processing_time=statistics.mean(processing_times),
                median_processing_time=statistics.median(processing_times),
                p95_processing_time=self._percentile(processing_times, 0.95),
                p99_processing_time=self._percentile(processing_times, 0.99),
                total_cost=sum(costs),
                avg_cost_per_query=statistics.mean(costs) if costs else 0.0,
                queries_by_tier=dict(queries_by_tier),
                queries_by_classification=dict(queries_by_classification),
                queries_by_model=dict(queries_by_model),
                error_rate=failed / total if total > 0 else 0.0,
                total_tokens=sum(q.tokens_used or 0 for q in queries)
            )
    
    
    def get_model_performance(self) -> List[ModelPerformance]:
        """Get performance metrics for all models"""
        with self._lock:
            performances = []
            
            for model_name in self.model_performance.keys():
                model_queries = [q for q in self.recent_queries if q.model_used == model_name]
                
                if not model_queries:
                    continue
                
                total = len(model_queries)
                successful = sum(1 for q in model_queries if q.success)
                errors = sum(1 for q in model_queries if not q.success)
                times = [q.processing_time for q in model_queries]
                costs = [q.cost or 0.0 for q in model_queries]
                
                performances.append(ModelPerformance(
                    model_name=model_name,
                    total_queries=total,
                    success_rate=successful / total if total > 0 else 0.0,
                    avg_response_time=statistics.mean(times) if times else 0.0,
                    avg_cost=statistics.mean(costs) if costs else 0.0,
                    error_count=errors,
                    last_used=max(q.timestamp for q in model_queries)
                ))
            
            return sorted(performances, key=lambda x: x.total_queries, reverse=True)
    
    
    def get_cost_analysis(self, time_window: Optional[int] = None) -> Dict:
        """Get detailed cost analysis"""
        metrics = self.get_aggregated_metrics(time_window)
        
        return {
            "total_cost": metrics.total_cost,
            "avg_cost_per_query": metrics.avg_cost_per_query,
            "cost_by_tier": self._calculate_cost_by_tier(),
            "projected_daily_cost": metrics.avg_cost_per_query * self._estimate_daily_queries(),
            "projected_monthly_cost": metrics.avg_cost_per_query * self._estimate_daily_queries() * 30,
            "cost_saved_by_cache": self._estimate_cache_savings(metrics)
        }
    
    
    def detect_anomalies(self) -> List[Dict]:
        """Detect performance anomalies"""
        anomalies = []
        metrics = self.get_aggregated_metrics(time_window=300)  # Last 5 minutes
        
        # Check error rate
        if metrics.error_rate > self.alert_thresholds["error_rate"]:
            anomalies.append({
                "type": "high_error_rate",
                "value": metrics.error_rate,
                "threshold": self.alert_thresholds["error_rate"],
                "severity": "high"
            })
        
        # Check processing time
        if metrics.avg_processing_time > self.alert_thresholds["avg_processing_time"]:
            anomalies.append({
                "type": "slow_processing",
                "value": metrics.avg_processing_time,
                "threshold": self.alert_thresholds["avg_processing_time"],
                "severity": "medium"
            })
        
        # Check P95 latency
        if metrics.p95_processing_time > self.alert_thresholds["p95_processing_time"]:
            anomalies.append({
                "type": "high_p95_latency",
                "value": metrics.p95_processing_time,
                "threshold": self.alert_thresholds["p95_processing_time"],
                "severity": "medium"
            })
        
        # Check cost
        if metrics.avg_cost_per_query > self.alert_thresholds["cost_per_query"]:
            anomalies.append({
                "type": "high_cost",
                "value": metrics.avg_cost_per_query,
                "threshold": self.alert_thresholds["cost_per_query"],
                "severity": "low"
            })
        
        return anomalies
    
    
    def _check_alerts(self):
        """Check for alert conditions"""
        anomalies = self.detect_anomalies()
        
        for anomaly in anomalies:
            alert = {
                "timestamp": time.time(),
                "datetime": datetime.now().isoformat(),
                **anomaly
            }
            self.alert_history.append(alert)
            
            # Print alert (in production, send to alerting system)
            print(f"⚠️ ALERT [{anomaly['severity'].upper()}]: {anomaly['type']}")
            print(f"   Value: {anomaly['value']:.4f} | Threshold: {anomaly['threshold']:.4f}")
    
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Get recent alerts"""
        return self.alert_history[-limit:]
    
    
    def export_metrics(self, output_file: str, time_window: Optional[int] = None):
        """Export metrics to JSON file"""
        metrics = self.get_aggregated_metrics(time_window)
        model_perf = self.get_model_performance()
        cost_analysis = self.get_cost_analysis(time_window)
        
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "aggregated_metrics": asdict(metrics),
            "model_performance": [asdict(m) for m in model_perf],
            "cost_analysis": cost_analysis,
            "recent_alerts": self.get_recent_alerts()
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Metrics exported to {output_file}")
    
    
    def print_dashboard(self):
        """Print monitoring dashboard"""
        metrics = self.get_aggregated_metrics(time_window=3600)  # Last hour
        model_perf = self.get_model_performance()
        
        print("\n" + "="*80)
        print("📊 LLM ROUTER - MONITORING DASHBOARD")
        print("="*80)
        
        print(f"\n⏱️  Last Hour Statistics:")
        print(f"   Total Queries: {metrics.total_queries}")
        print(f"   Success Rate: {metrics.success_rate:.2%}")
        print(f"   Error Rate: {metrics.error_rate:.2%}")
        print(f"   Cache Hit Rate: {metrics.cache_hit_rate:.2%}")
        
        print(f"\n⚡ Performance:")
        print(f"   Avg Processing Time: {metrics.avg_processing_time:.2f}s")
        print(f"   Median: {metrics.median_processing_time:.2f}s")
        print(f"   P95: {metrics.p95_processing_time:.2f}s")
        print(f"   P99: {metrics.p99_processing_time:.2f}s")
        
        print(f"\n💰 Cost Analysis:")
        print(f"   Total Cost: ${metrics.total_cost:.4f}")
        print(f"   Avg Cost/Query: ${metrics.avg_cost_per_query:.4f}")
        print(f"   Total Tokens: {metrics.total_tokens:,}")
        
        print(f"\n📈 Distribution:")
        print(f"   By Tier:")
        for tier, count in sorted(metrics.queries_by_tier.items()):
            percentage = (count / metrics.total_queries * 100) if metrics.total_queries > 0 else 0
            print(f"      {tier}: {count} ({percentage:.1f}%)")
        
        print(f"\n🎯 By Classification:")
        for cls, count in sorted(metrics.queries_by_classification.items()):
            percentage = (count / metrics.total_queries * 100) if metrics.total_queries > 0 else 0
            print(f"      {cls}: {count} ({percentage:.1f}%)")
        
        print(f"\n🤖 Top Models:")
        for i, perf in enumerate(model_perf[:5], 1):
            print(f"   {i}. {perf.model_name}")
            print(f"      Queries: {perf.total_queries} | Success: {perf.success_rate:.2%} | Avg Time: {perf.avg_response_time:.2f}s")
        
        # Show alerts if any
        recent_alerts = self.get_recent_alerts(5)
        if recent_alerts:
            print(f"\n⚠️  Recent Alerts:")
            for alert in recent_alerts:
                print(f"   [{alert['severity'].upper()}] {alert['type']}: {alert.get('value', 'N/A')}")
        
        print("\n" + "="*80 + "\n")
    
    
    # Helper methods
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    
    def _empty_metrics(self) -> AggregatedMetrics:
        """Return empty metrics"""
        return AggregatedMetrics(
            total_queries=0,
            successful_queries=0,
            failed_queries=0,
            success_rate=0.0,
            cache_hit_rate=0.0,
            avg_processing_time=0.0,
            median_processing_time=0.0,
            p95_processing_time=0.0,
            p99_processing_time=0.0,
            total_cost=0.0,
            avg_cost_per_query=0.0,
            queries_by_tier={},
            queries_by_classification={},
            queries_by_model={},
            error_rate=0.0,
            total_tokens=0
        )
    
    
    def _calculate_cost_by_tier(self) -> Dict[str, float]:
        """Calculate total cost by tier"""
        cost_by_tier = defaultdict(float)
        
        for query in self.recent_queries:
            cost_by_tier[query.tier] += query.cost or 0.0
        
        return dict(cost_by_tier)
    
    
    def _estimate_daily_queries(self) -> int:
        """Estimate daily query volume"""
        if not self.recent_queries:
            return 0
        
        # Calculate queries per second from recent data
        time_span = time.time() - self.recent_queries[0].timestamp
        if time_span == 0:
            return 0
        
        qps = len(self.recent_queries) / time_span
        return int(qps * 86400)  # 24 hours
    
    
    def _estimate_cache_savings(self, metrics: AggregatedMetrics) -> float:
        """Estimate cost saved by caching"""
        if metrics.total_queries == 0:
            return 0.0
        
        cache_hits = int(metrics.total_queries * metrics.cache_hit_rate)
        return cache_hits * metrics.avg_cost_per_query
