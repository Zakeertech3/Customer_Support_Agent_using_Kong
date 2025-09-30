#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from scripts.generate_demo_data import DemoDataGenerator

def test_demo_generation():
    print("Testing demo data generation...")
    
    generator = DemoDataGenerator()
    
    # Test conversation generation
    conversations = generator.generate_demo_conversations(5)
    print(f"Generated {len(conversations)} demo conversations")
    
    # Test performance data
    perf_data = generator.generate_performance_test_data()
    print(f"Generated performance test data with {len(perf_data['concurrent_test_queries'])} queries")
    
    # Test scenarios by category
    scenarios = generator.get_test_scenarios_by_category()
    print(f"Generated scenarios for {len(scenarios)} categories")
    
    # Save demo data
    generator.save_demo_data("test_demo_data.json")
    
    print("✅ Demo data generation test completed successfully")
    return True

if __name__ == "__main__":
    try:
        success = test_demo_generation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Demo data generation test failed: {e}")
        sys.exit(1)