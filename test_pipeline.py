import os
from src.candidate_ranker import CandidateRanker

sample_dir = os.path.join('data', 'sample')
with open(os.path.join(sample_dir, 'job_description.txt'), 'r', encoding='utf-8') as f:
    job_desc = f.read()

resumes = []
for fname in ['alex_rivera_senior_ml.txt', 'sarah_chen_data_analyst.txt', 'michael_scott_frontend.txt']:
    with open(os.path.join(sample_dir, fname), 'rb') as f:
        resumes.append({'filename': fname, 'content': f.read()})

ranker = CandidateRanker()
results = ranker.process_candidates(job_desc, resumes)

print("="*60)
print("AI RESUME SCREENING PIPELINE RESULTS")
print("="*60)
print(f"TOTAL CANDIDATES PROCESSED: {results['total_processed']}")
print(f"REQUIRED SKILLS IDENTIFIED IN JOB: {results['job_required_skills']}\n")

for c in results['candidates']:
    print(f"{c['rank_str']} | {c['candidate_name']:<20} | Score: {c['overall_match_score']}% | Status: {c['status']}")
    print(f"   Experience: {c['experience_years']} years | Email: {c['email']} | Phone: {c['phone']}")
    print(f"   Matched Skills ({len(c['matched_skills'])}): {', '.join(c['matched_skills'])}")
    print(f"   Missing Skills ({len(c['missing_skills'])}): {', '.join(c['missing_skills'])}\n")
print("="*60)
