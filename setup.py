from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="intelligent-log-analysis",
    version="0.1.0",
    description="Intelligent OS log analysis and prediction system using ML and pattern recognition",
    author="Intelligent Log Analysis Team",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={
        "console_scripts": [
            "intelligent-log-analysis=intelligent_log_analysis.main:main",
        ],
    },
)