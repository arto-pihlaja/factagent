"""
Test script for Fact-Checker Agent
"""

from agent import run_fact_checker

print("=" * 70)
print("FACT-CHECKER AGENT TEST")
print("=" * 70)

# Test 1: YouTube video summary
print("\n[Test 1] YouTube Video Summary")
print("-" * 70)
url = "https://www.youtube.com/watch?v=aircAruvnKk"
print(f"URL: {url}")
print("Enable fact-check: False")
print("\nRunning agent...\n")

try:
    result = run_fact_checker(url, enable_fact_check=False)
    print("RESULT:")
    print("-" * 70)
    print(result)
    print("-" * 70)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Test completed!")
