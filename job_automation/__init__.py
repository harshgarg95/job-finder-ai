"""job_automation — scraping and aggregation utilities."""
from .job_scraper import scrape_jobs, JobScraper
from .aggregator import JobAggregator
from .naukri_scraper import NaukriScraper

__all__ = ["scrape_jobs", "JobScraper", "JobAggregator", "NaukriScraper"]
