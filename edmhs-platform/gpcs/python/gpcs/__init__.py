"""GPCS: Grant Proposal Creation System (EDMHS)."""
from .solicitation import Solicitation, parse, parse_text
from .packages import PACKAGES, select_package
from .applicant import load_profile, NonprofitProfile, ForProfitProfile
from .knowledge import KnowledgeBase
from .crosswalk import build_crosswalk

__all__ = ["Solicitation", "parse", "parse_text", "PACKAGES", "select_package", "load_profile",
           "NonprofitProfile", "ForProfitProfile", "KnowledgeBase", "build_crosswalk"]
__version__ = "0.1.0"
