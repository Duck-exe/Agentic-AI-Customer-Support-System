import time
from app.agents import detect_intents

TESTS = [
    ("I was charged twice this month", {"billing"}),
    ("Please send my invoice", {"billing"}),
    ("I cannot login after resetting my password", {"technical"}),
    ("The application crashes during installation", {"technical"}),
    ("What is included in Premium?", {"product"}),
    ("Compare Basic and Premium pricing", {"product"}),
    ("This service is unacceptable and I want to complain", {"complaint"}),
    ("I paid yesterday but Premium is still locked", {"billing","technical"}),
    ("What are your support hours?", {"faq"}),
]
correct=0; times=[]
for query, expected in TESTS:
    start=time.perf_counter()
    got=set(detect_intents(query))
    times.append((time.perf_counter()-start)*1000)
    ok=expected.issubset(got)
    correct += int(ok)
    print(f"{'PASS' if ok else 'FAIL'} | expected={sorted(expected)} got={sorted(got)} | {query}")
print(f"Routing accuracy: {correct}/{len(TESTS)} = {correct/len(TESTS):.1%}")
print(f"Average routing latency: {sum(times)/len(times):.3f} ms")
