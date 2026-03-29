# 🤖 ROS 2 지능형 듀플로 조립 로봇 (Intelligent Duplo Assembly Robot)

![ROS 2](https://img.shields.io/badge/ROS_2-Humble-22314E?style=flat&logo=ros&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat&logo=python&logoColor=white)
![YOLO](https://img.shields.io/badge/YOLO-Vision-00FFFF?style=flat&logo=yolo&logoColor=black)
![RealSense](https://img.shields.io/badge/Intel_RealSense-RGBD-0071C5?style=flat&logo=intel&logoColor=white)

## 📌 프로젝트 개요 (Overview)
본 프로젝트는 ROS 2 환경에서 **RGB-D 카메라(RealSense)와 객체 인식 모델(YOLO)을 활용하여 듀플로 블록을 스스로 스캔하고 최적의 조합을 찾아 조립하는 지능형 로봇 팔 제어 시스템**입니다. 

단순히 하드코딩된 시퀀스를 따르는 것을 넘어, 카메라로 현재 필드의 블록 인벤토리를 파악하고 **DFS(깊이 우선 탐색) 알고리즘**을 통해 남는 블록이 최소화되는 최적의 조립 계획을 스스로 수립합니다.

## 🧱 조립 가능한 듀플로 레시피 (Assembly Recipes)
총 7가지의 다양한 듀플로 조합 패턴을 인식하고 조립할 수 있습니다.
* **2단 조합:** 🔋 배터리(노+파), 🧲 자석(파+빨), 🛑 비상정지(빨+노_십자)
* **3단 조합:** 🥕 당근(초+노+노), 🚦 신호등(빨+노+초), 🌳 작은 나무(빨_4x2+노+빨), 🔨 망치(파_4x2+빨+빨_90도)

---

## 🚀 핵심 기능 및 기술 (Key Features & Tech)

### 1. 인벤토리 스캔 및 DFS 최적화 조립 (Inventory Scan & DFS Optimization)
* **문제점:** 기존의 탐욕적(Greedy) 실행 방식은 필드에 전체 조합을 완성할 블록이 부족해도 일단 눈앞에 보이는 블록을 집어 들어 중간에 에러가 발생하는 한계가 있었습니다.
* **해결책:** 조립 시작 전, 비전 노드에 `count_` 요청을 보내 필드의 모든 블록 종류와 개수를 파악합니다. 수집된 인벤토리 데이터를 바탕으로 **DFS 알고리즘 기반의 가상 시뮬레이션**을 돌려, 버려지는 블록이 가장 적은 최적의 조립 순서를 찾아내어 실행합니다.

### 2. 1층 Z-Depth 필터링 (Z-Depth Ground Filtering)
* **문제점:** 2D 객체 인식의 한계로 인해, 조립이 완료된 타워의 꼭대기 층 블록(예: 완성된 신호등의 노란색)을 바닥에 있는 재료 블록으로 착각하여 다시 뜯어버리는 치명적인 논리 오류가 발생했습니다.
* **해결책:** RealSense 카메라의 Depth 데이터를 활용하여, YOLO가 인식한 타겟 중 **Z값(카메라와의 거리)이 가장 큰(즉, 가장 바닥에 위치한) 블록들만 필터링하여 1층 재료로만 타겟팅**하도록 비전 노드를 고도화했습니다.

### 3. 메모리 기반 블라인드 스택 (Dead Reckoning & Blind Stack)
* **문제점:** 블록을 쌓을 때마다 카메라로 정밀 스캔을 하면, 로봇 그리퍼에 의해 시야가 가려지는 오클루전(Occlusion) 현상이 발생하고 조립 속도가 크게 저하됩니다.
* **해결책:** 조립의 1단계(베이스 블록) 좌표만 카메라로 정밀하게 스캔하여 마스터 노드 메모리에 저장합니다. 2층 이상을 쌓을 때는 **카메라 스캔 없이 메모리된 (X, Y) 좌표로 바로 이동한 뒤, 블록 높이(`BLOCK_H`)만큼만 Z축을 계산하여 꽂아 넣는 블라인드 스택 기법**을 도입하여 인식 오류율을 0%로 만들고 조립 속도를 2배 이상 향상시켰습니다.

---

## 👨‍💻 Author
* **이다한 (Lee Dahan)**
* Incheon National University, Dept. of Electrical Engineering# duplo_ws
