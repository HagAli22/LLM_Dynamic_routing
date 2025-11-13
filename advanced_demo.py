"""
Advanced Demo - Showcase of Professional Features
=================================================
Demonstrates all professional features of the Enhanced LLM Router System.

Features Demonstrated:
- Advanced monitoring and metrics
- Rate limiting and DDoS protection
- Quality evaluation
- A/B testing framework
- Complete workflow
"""

import time
from main2 import DynamicLLMRouter
from ab_testing import Variant
import random


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def demo_basic_routing():
    """Demo 1: Basic routing with all features"""
    print_header("DEMO 1: BASIC ROUTING WITH PROFESSIONAL FEATURES")
    
    # Initialize router with all features
    router = DynamicLLMRouter(
        cache_ttl=600,
        enable_logging=True,
        enable_monitoring=True,
        enable_rate_limiting=True,
        enable_quality_eval=True,
        enable_ab_testing=False,
        user_tier="premium"
    )
    
    # Test queries
    queries = [
        "What is Python?",
        "Explain machine learning in detail",
        "Create a complete REST API with authentication in Python"
    ]
    
    print("🚀 Processing queries...\n")
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'─'*80}")
        print(f"Query {i}: {query}")
        print('─'*80)
        
        response = router.process_query(
            query=query,
            user_id=f"user_{i}",
            ip_address=f"192.168.1.{i}"
        )
        
        print(f"\n✅ Success: {response.success}")
        print(f"📊 Classification: {response.classification} | Tier: {response.model_tier}")
        print(f"🤖 Model: {response.used_model}")
        print(f"⚡ Time: {response.processing_time:.2f}s | Cache: {response.cache_hit}")
        
        # Show quality score
        if response.quality_score:
            qs = response.quality_score
            print(f"\n📈 Quality Score: {qs['overall_score']:.1f}/100")
            print(f"   - Relevance: {qs['relevance']:.1f}")
            print(f"   - Coherence: {qs['coherence']:.1f}")
            print(f"   - Completeness: {qs['completeness']:.1f}")
            print(f"   - Recommendation: {qs['recommendation']}")
        
        # Show rate limit info
        if response.rate_limit_info:
            print(f"\n🚦 Rate Limits:")
            print(f"   - Remaining (minute): {response.rate_limit_info.get('X-RateLimit-Remaining-Minute')}")
            print(f"   - Remaining (hour): {response.rate_limit_info.get('X-RateLimit-Remaining-Hour')}")
        
        print(f"\n💬 Response Preview: {response.response[:200]}...")
        
        time.sleep(1)  # Small delay between requests
    
    # Show statistics
    print_header("SYSTEM STATISTICS")
    router.print_stats()
    
    return router


def demo_rate_limiting():
    """Demo 2: Rate limiting in action"""
    print_header("DEMO 2: RATE LIMITING & DDOS PROTECTION")
    
    router = DynamicLLMRouter(
        enable_logging=True,
        enable_rate_limiting=True,
        user_tier="free"  # Limited tier
    )
    
    print("📝 Testing rate limits with 'free' tier (5 requests/minute)...\n")
    
    # Try to make many requests quickly
    for i in range(8):
        response = router.process_query(
            query="What is AI?",
            user_id="test_user",
            ip_address="192.168.1.100"
        )
        
        print(f"Request {i+1}: ", end="")
        if response.success:
            print(f"✅ Success")
        else:
            print(f"❌ Rate limited - {response.error}")
        
        time.sleep(0.1)
    
    # Show rate limit statistics
    print("\n📊 Rate Limit Statistics:")
    stats = router.get_rate_limit_stats()
    print(f"   Active users: {stats.get('active_users', 0)}")
    print(f"   Total violations: {stats.get('total_violations', 0)}")
    
    return router


def demo_monitoring():
    """Demo 3: Advanced monitoring"""
    print_header("DEMO 3: ADVANCED MONITORING & ANALYTICS")
    
    router = DynamicLLMRouter(
        enable_logging=False,
        enable_monitoring=True,
        user_tier="premium"
    )
    
    print("📊 Generating traffic for monitoring...\n")
    
    # Simulate various queries
    test_scenarios = [
        ("Simple", ["What is 2+2?", "Capital of France?", "Define AI"]),
        ("Medium", ["Explain quantum computing", "How does blockchain work?"]),
        ("Complex", ["Design a microservices architecture", "Implement binary search tree"])
    ]
    
    for category, queries in test_scenarios:
        print(f"\n{category} Queries:")
        for query in queries:
            response = router.process_query(
                query=query,
                user_id=f"user_{random.randint(1, 5)}",
                ip_address=f"192.168.1.{random.randint(1, 50)}"
            )
            status = "✅" if response.success else "❌"
            print(f"   {status} {query[:50]}")
            time.sleep(0.2)
    
    # Display monitoring dashboard
    print_header("MONITORING DASHBOARD")
    router.get_monitoring_dashboard()
    
    # Export metrics
    print("\n💾 Exporting metrics...")
    router.export_monitoring_data("metrics_export.json")
    
    return router


def demo_quality_evaluation():
    """Demo 4: Quality evaluation"""
    print_header("DEMO 4: RESPONSE QUALITY EVALUATION")
    
    router = DynamicLLMRouter(
        enable_logging=True,
        enable_quality_eval=True,
        user_tier="premium"
    )
    
    test_queries = [
        "What is Python?",
        "Explain the theory of relativity",
        "Write a sorting algorithm"
    ]
    
    print("🔍 Evaluating response quality...\n")
    
    for query in test_queries:
        print(f"\n{'─'*80}")
        print(f"Query: {query}")
        print('─'*80)
        
        response = router.process_query(query=query, user_id="quality_test_user")
        
        if response.quality_score:
            qs = response.quality_score
            
            print(f"\n📊 Quality Metrics:")
            print(f"   Overall Score: {qs['overall_score']:.1f}/100")
            print(f"   Relevance: {qs['relevance']:.1f}/100")
            print(f"   Coherence: {qs['coherence']:.1f}/100")
            print(f"   Completeness: {qs['completeness']:.1f}/100")
            print(f"   Accuracy: {qs['accuracy']:.1f}/100")
            print(f"   Safety: {qs['safety']:.1f}/100")
            print(f"   Fluency: {qs['fluency']:.1f}/100")
            
            print(f"\n🎯 Recommendation: {qs['recommendation'].upper()}")
            
            if qs['flags']:
                print(f"⚠️  Flags: {', '.join(qs['flags'])}")
            
            if qs['feedback']:
                print(f"\n💡 Feedback:")
                for feedback in qs['feedback']:
                    print(f"   - {feedback}")
        
        time.sleep(1)
    
    return router


def demo_ab_testing():
    """Demo 5: A/B testing"""
    print_header("DEMO 5: A/B TESTING FRAMEWORK")
    
    router = DynamicLLMRouter(
        enable_logging=True,
        enable_ab_testing=True,
        user_tier="enterprise"
    )
    
    if not router.ab_testing:
        print("⚠️ A/B testing not initialized")
        return None
    
    # Create A/B test
    print("📝 Creating A/B test: 'Model Performance Comparison'\n")
    
    variants = [
        Variant(
            name="Variant A",
            model="meta-llama/llama-3.3-70b-instruct:free",
            traffic_percentage=50.0,
            description="Llama 3.3 70B model"
        ),
        Variant(
            name="Variant B",
            model="qwen/qwen-2.5-72b-instruct:free",
            traffic_percentage=50.0,
            description="Qwen 2.5 72B model"
        )
    ]
    
    test_id = router.ab_testing.create_test(
        test_name="Model Performance Comparison",
        variants=variants,
        duration=300,  # 5 minutes
        min_samples=10
    )
    
    print(f"✅ Test created with ID: {test_id}\n")
    
    # Simulate test queries
    print("🚀 Simulating test traffic...\n")
    
    test_queries = [
        "What is artificial intelligence?",
        "Explain how neural networks work",
        "What are the benefits of cloud computing?",
    ] * 5  # Repeat to get more samples
    
    for i, query in enumerate(test_queries[:15], 1):  # Limit for demo
        response = router.process_query(
            query=query,
            user_id=f"test_user_{i % 5}",
            ab_test_id=test_id
        )
        
        variant = response.ab_test_variant or "Unknown"
        print(f"{i}. Variant: {variant} | Success: {response.success} | Time: {response.processing_time:.2f}s")
        
        time.sleep(0.5)
    
    # Check test status
    print(f"\n{'─'*80}")
    print("📊 A/B Test Status")
    print('─'*80)
    
    test_status = router.ab_testing.get_test_status(test_id)
    if test_status:
        print(f"\nTest: {test_status['test_name']}")
        print(f"Status: {test_status['status']}")
        print(f"Runtime: {test_status['runtime']:.0f}s")
        
        print("\nVariant Metrics:")
        for variant_name, metrics in test_status['metrics'].items():
            print(f"\n  {variant_name}:")
            print(f"    Total Queries: {metrics['total_queries']}")
            print(f"    Success Rate: {metrics['successful_queries'] / max(metrics['total_queries'], 1) * 100:.1f}%")
            print(f"    Avg Response Time: {metrics['avg_response_time']:.2f}s")
            print(f"    Avg Quality Score: {metrics['avg_quality_score']:.2f}")
        
        if test_status['winner']:
            print(f"\n🏆 Current Leader: {test_status['winner']} (Confidence: {test_status['confidence']:.1f}%)")
    
    return router


def demo_comprehensive():
    """Demo 6: Comprehensive demo with all features"""
    print_header("DEMO 6: COMPREHENSIVE SYSTEM TEST")
    
    router = DynamicLLMRouter(
        cache_ttl=600,
        enable_logging=True,
        enable_monitoring=True,
        enable_rate_limiting=True,
        enable_quality_eval=True,
        enable_ab_testing=False,
        user_tier="enterprise"
    )
    
    print("🎯 Running comprehensive system test...\n")
    
    # Test various scenarios
    scenarios = [
        {
            "name": "Cache Test",
            "queries": ["What is Python?", "What is Python?"],  # Duplicate for cache
            "user": "cache_user",
            "ip": "192.168.1.10"
        },
        {
            "name": "Different Tiers",
            "queries": [
                "What is 2+2?",
                "Explain quantum mechanics briefly",
                "Design a distributed system architecture"
            ],
            "user": "tier_user",
            "ip": "192.168.1.20"
        },
        {
            "name": "Quality Check",
            "queries": ["Explain machine learning"],
            "user": "quality_user",
            "ip": "192.168.1.30"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{'─'*80}")
        print(f"Scenario: {scenario['name']}")
        print('─'*80)
        
        for query in scenario['queries']:
            response = router.process_query(
                query=query,
                user_id=scenario['user'],
                ip_address=scenario['ip']
            )
            
            print(f"\n📝 Query: {query[:60]}")
            print(f"   Status: {'✅ Success' if response.success else '❌ Failed'}")
            print(f"   Classification: {response.classification} | Tier: {response.model_tier}")
            print(f"   Cache: {'HIT 💾' if response.cache_hit else 'MISS'}")
            print(f"   Time: {response.processing_time:.2f}s")
            
            if response.quality_score:
                print(f"   Quality: {response.quality_score['overall_score']:.1f}/100 ({response.quality_score['recommendation']})")
            
            time.sleep(0.5)
    
    # Final dashboard
    print_header("FINAL SYSTEM DASHBOARD")
    router.get_monitoring_dashboard()
    
    print("\n" + "="*80)
    print("  SYSTEM FEATURES SUMMARY")
    print("="*80)
    print(f"  ✅ Advanced Monitoring & Analytics")
    print(f"  ✅ Rate Limiting & DDoS Protection")
    print(f"  ✅ Quality Evaluation System")
    print(f"  ✅ A/B Testing Framework")
    print(f"  ✅ Semantic Caching")
    print(f"  ✅ Dynamic Model Routing")
    print(f"  ✅ Fallback Mechanisms")
    print(f"  ✅ Comprehensive Logging")
    print("="*80 + "\n")
    
    return router


def main():
    """Main demo runner"""
    print("\n" + "="*80)
    print("  ENHANCED LLM ROUTER SYSTEM - PROFESSIONAL FEATURES DEMO")
    print("="*80)
    print("\nThis demo showcases the professional features added to the system:")
    print("  1. Basic Routing with Professional Features")
    print("  2. Rate Limiting & DDoS Protection")
    print("  3. Advanced Monitoring & Analytics")
    print("  4. Response Quality Evaluation")
    print("  5. A/B Testing Framework")
    print("  6. Comprehensive System Test")
    print("\n" + "="*80)
    
    demos = {
        "1": ("Basic Routing", demo_basic_routing),
        "2": ("Rate Limiting", demo_rate_limiting),
        "3": ("Monitoring", demo_monitoring),
        "4": ("Quality Evaluation", demo_quality_evaluation),
        "5": ("A/B Testing", demo_ab_testing),
        "6": ("Comprehensive Test", demo_comprehensive)
    }
    
    choice = input("\nSelect demo to run (1-6, or 'all' for all demos): ").strip()
    
    if choice.lower() == "all":
        for name, demo_func in demos.values():
            try:
                demo_func()
                input("\n\nPress Enter to continue to next demo...")
            except Exception as e:
                print(f"\n❌ Demo failed: {e}")
    elif choice in demos:
        name, demo_func = demos[choice]
        try:
            demo_func()
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
    else:
        print("❌ Invalid choice")
    
    print("\n" + "="*80)
    print("  DEMO COMPLETED!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
