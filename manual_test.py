"""Quick manual test for the interviewer + report logic, run directly from the
terminal before the HTTP layer exists. Not part of the app itself.

Usage:
    source venv/bin/activate
    python manual_test.py
"""

from app.interviewer import get_next_message
from app.report import generate_report
from app.schemas import Message

if __name__ == "__main__":
    topic = input("Topic: ").strip() or "Binary Trees"
    difficulty = input("Difficulty (Easy/Medium/Hard): ").strip() or "Easy"

    history: list[Message] = []

    while True:
        reply = get_next_message(topic, difficulty, history)
        print(f"\nInterviewer: {reply.message}")

        if reply.is_complete:
            print("\n--- Interview ended. Generating report... ---\n")
            break

        history.append(Message(role="interviewer", content=reply.message))
        answer = input("You: ").strip()
        history.append(Message(role="candidate", content=answer))

    report = generate_report(topic, difficulty, history)
    print(f"Score: {report.score} ({report.band}) — {report.result}")
    print(f"Verdict: {report.verdict}")
    print(f"Strengths: {report.strengths}")
    print(f"Weaknesses: {report.weaknesses}")
    print(f"Topics to revise: {report.topics_to_revise}")
