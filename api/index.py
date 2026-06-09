import sys
import os

# 프로젝트 루트(api의 상위 폴더)를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
