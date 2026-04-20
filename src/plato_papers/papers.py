"""Research paper management — citation tracking, bibliography, search, and knowledge graph."""
import time
import re
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict
from enum import Enum

class PaperStatus(Enum):
    UNREAD = "unread"
    READING = "reading"
    ANNOTATED = "annotated"
    SUMMARIZED = "summarized"
    INTEGRATED = "integrated"

class PaperType(Enum):
    RESEARCH = "research"
    TUTORIAL = "tutorial"
    SURVEY = "survey"
    PREPRINT = "preprint"
    TECH_REPORT = "tech_report"
    BLOG = "blog"
    ARXIV = "arxiv"

@dataclass
class Paper:
    id: str
    title: str
    authors: list[str] = field(default_factory=list)
    year: int = 2024
    abstract: str = ""
    paper_type: PaperType = PaperType.RESEARCH
    url: str = ""
    arxiv_id: str = ""
    doi: str = ""
    tags: list[str] = field(default_factory=list)
    status: PaperStatus = PaperStatus.UNREAD
    relevance_score: float = 0.0
    citations_in: int = 0
    citations_out: list[str] = field(default_factory=list)
    key_insights: list[str] = field(default_factory=list)
    summary: str = ""
    domain: str = ""
    added_at: float = field(default_factory=time.time)
    read_at: float = 0.0
    metadata: dict = field(default_factory=dict)

@dataclass
class Citation:
    source_paper: str
    target_paper: str
    context: str = ""
    strength: float = 0.5

@dataclass
class LiteratureReview:
    topic: str
    papers: list[str] = field(default_factory=list)
    synthesis: str = ""
    gaps: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

class PaperManager:
    def __init__(self):
        self._papers: dict[str, Paper] = {}
        self._citations: dict[str, list[Citation]] = defaultdict(list)
        self._reviews: dict[str, LiteratureReview] = {}
        self._reading_queue: list[str] = []

    def add(self, paper: Paper) -> Paper:
        self._papers[paper.id] = paper
        if paper.status == PaperStatus.UNREAD:
            self._reading_queue.append(paper.id)
        return paper

    def get(self, paper_id: str) -> Optional[Paper]:
        return self._papers.get(paper_id)

    def add_citation(self, source: str, target: str, context: str = "", strength: float = 0.5):
        citation = Citation(source_paper=source, target_paper=target, context=context, strength=strength)
        self._citations[source].append(citation)
        if target in self._papers:
            self._papers[target].citations_in += 1
        if source in self._papers:
            self._papers[source].citations_out.append(target)

    def search(self, query: str, limit: int = 20) -> list[Paper]:
        query_lower = query.lower()
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        scored = []
        for paper in self._papers.values():
            score = 0.0
            text = f"{paper.title} {paper.abstract} {' '.join(paper.tags)}".lower()
            if query_lower in text:
                score += 2.0
            for word in query_words:
                if word in text:
                    score += 0.3
            if any(tag.lower() in query_lower for tag in paper.tags):
                score += 1.0
            score *= (1 + paper.relevance_score)
            if score > 0:
                scored.append((paper, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in scored[:limit]]

    def by_status(self, status: PaperStatus) -> list[Paper]:
        return [p for p in self._papers.values() if p.status == status]

    def by_domain(self, domain: str) -> list[Paper]:
        return [p for p in self._papers.values() if p.domain == domain]

    def by_author(self, author: str) -> list[Paper]:
        return [p for p in self._papers.values() if any(author.lower() in a.lower() for a in p.authors)]

    def by_tag(self, tag: str) -> list[Paper]:
        return [p for p in self._papers.values() if tag in p.tags]

    def most_cited(self, n: int = 10) -> list[Paper]:
        papers = list(self._papers.values())
        papers.sort(key=lambda p: p.citations_in, reverse=True)
        return papers[:n]

    def next_to_read(self, n: int = 5) -> list[Paper]:
        queue = [self._papers[pid] for pid in self._reading_queue
                 if pid in self._papers and self._papers[pid].status == PaperStatus.UNREAD]
        queue.sort(key=lambda p: p.relevance_score, reverse=True)
        return queue[:n]

    def mark_reading(self, paper_id: str):
        paper = self._papers.get(paper_id)
        if paper:
            paper.status = PaperStatus.READING
            paper.read_at = time.time()

    def add_insight(self, paper_id: str, insight: str):
        paper = self._papers.get(paper_id)
        if paper:
            paper.key_insights.append(insight)
            if paper.status == PaperStatus.READING:
                paper.status = PaperStatus.ANNOTATED

    def set_summary(self, paper_id: str, summary: str):
        paper = self._papers.get(paper_id)
        if paper:
            paper.summary = summary
            paper.status = PaperStatus.SUMMARIZED

    def create_review(self, topic: str, paper_ids: list[str]) -> LiteratureReview:
        review = LiteratureReview(topic=topic, papers=paper_ids)
        self._reviews[topic] = review
        return review

    def citation_graph(self, paper_id: str) -> dict:
        outgoing = [c.target_paper for c in self._citations.get(paper_id, [])]
        incoming = [c.source_paper for c in self._citations.get(paper_id, [])]
        return {"outgoing": outgoing, "incoming": incoming, "total": len(outgoing) + len(incoming)}

    def tags(self) -> dict[str, int]:
        counts = defaultdict(int)
        for paper in self._papers.values():
            for tag in paper.tags:
                counts[tag] += 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def authors(self) -> dict[str, int]:
        counts = defaultdict(int)
        for paper in self._papers.values():
            for author in paper.authors:
                counts[author] += 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def domains(self) -> dict[str, int]:
        counts = defaultdict(int)
        for paper in self._papers.values():
            counts[paper.domain] += 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    @property
    def stats(self) -> dict:
        statuses = defaultdict(int)
        for p in self._papers.values():
            statuses[p.status.value] += 1
        return {"papers": len(self._papers), "statuses": dict(statuses),
                "citations": sum(len(c) for c in self._citations.values()),
                "reviews": len(self._reviews), "reading_queue": len(self._reading_queue),
                "domains": len(self.domains()), "tags": len(self.tags())}
