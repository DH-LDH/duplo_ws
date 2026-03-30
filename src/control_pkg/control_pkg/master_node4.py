# import rclpy
# from rclpy.node import Node
# from srvs_pkg.srv import GetTargetPose
# from std_srvs.srv import SetBool, Trigger
# import time
# import math

# class MasterNode(Node):
#     def __init__(self):
#         super().__init__('master_node')
#         self.cli_v = self.create_client(GetTargetPose, '/get_target_pose')
#         self.cli_r = self.create_client(GetTargetPose, '/robot_move_step')
#         self.cli_g = self.create_client(SetBool, '/control_gripper')
#         self.cli_h = self.create_client(Trigger, '/robot_home')
        
#         self.Z_OFF = -85.0
#         self.Z_MARGIN = 20.0
#         self.BLOCK_H = 16.0
#         self.WAIT_TIME = 1.5 
        
#         self.STUD_PITCH = 0.016 
#         self.YAW_TUNE = 0.0  # 필요시 여기서 영점 조절 (예: -1.5)

#     def call(self, cli, req):
#         while not cli.wait_for_service(timeout_sec=1.0):
#             self.get_logger().info(f'Waiting for {cli.srv_name}...')
#         future = cli.call_async(req)
#         rclpy.spin_until_future_complete(self, future)
#         return future.result()

#     def count_color(self, color):
#         p = self.call(self.cli_v, GetTargetPose.Request(target_color=f"count_{color}"))
#         return int(p.x) if p.success else 0

#     def find_target_with_retry(self, color, retries=4):
#         for i in range(retries):
#             p = self.call(self.cli_v, GetTargetPose.Request(target_color=color))
#             if p.success:
#                 return p
#             self.get_logger().warn(f"⚠️ [{color}] 타겟 찾는 중... ({i+1}/{retries})")
#             time.sleep(1.0) 
#         return None

#     def pick_target(self, color):
#         self.get_logger().info(f"\n--- PICK TARGET: [{color.upper()}] ---")
#         p = self.find_target_with_retry(color)
#         if not p: return False
        
#         req = GetTargetPose.Request(); req.yaw = p.yaw; req.target_size = "YAW"
#         self.call(self.cli_r, req)
#         time.sleep(self.WAIT_TIME) 

#         p = self.find_target_with_retry(color)
#         if not p: return False
#         req = GetTargetPose.Request(); req.x = p.x; req.y = p.y; req.target_size = "XY"
#         self.call(self.cli_r, req)
#         time.sleep(self.WAIT_TIME) 

#         p = self.find_target_with_retry(color)
#         if not p: return False
#         z_move = p.z * 1000.0 + self.Z_OFF
#         self.call(self.cli_r, GetTargetPose.Request(z=z_move - self.Z_MARGIN, target_size="Z"))
#         time.sleep(self.WAIT_TIME) 
#         self.call(self.cli_r, GetTargetPose.Request(z=self.Z_MARGIN, target_size="Z"))
#         time.sleep(self.WAIT_TIME) 

#         self.call(self.cli_g, SetBool.Request(data=True))
#         time.sleep(self.WAIT_TIME) 
#         self.call(self.cli_r, GetTargetPose.Request(z=-50.0, target_size="Z"))
#         time.sleep(self.WAIT_TIME) 
#         return True

#     def visual_insert(self, target_color, layer_index, yaw_offset=0.0, offset_studs_x=0.0, offset_studs_y=0.0):
#         self.get_logger().info(f"\n--- VISUAL STACK: [{target_color.upper()}] (Layer +{layer_index}, Y Offset: {offset_studs_y}) ---")
#         time.sleep(1.0)

#         # 1. 첫 번째 시각 확인: 타겟을 보고 YAW부터 맞춤
#         p = self.find_target_with_retry(target_color)
#         if not p: return False
        
#         target_yaw = p.yaw + yaw_offset + self.YAW_TUNE
#         while target_yaw > 90.0: target_yaw -= 180.0
#         while target_yaw < -90.0: target_yaw += 180.0

#         if abs(target_yaw) < 0.1:
#             self.get_logger().info(f"⏭️ [Skip YAW] 각도 오차 생략")
#         else:
#             self.get_logger().info(f"🔄 [YAW 회전] 시각 보정 기반 회전: {target_yaw:.1f}도")
#             req_y = GetTargetPose.Request()
#             req_y.yaw = target_yaw; req_y.target_size = "YAW"
#             self.call(self.cli_r, req_y)
#             time.sleep(self.WAIT_TIME)

#         # 2. 두 번째 시각 확인: YAW가 정렬된 상태에서 카메라로 정확한 XY 재추출
#         p = self.find_target_with_retry(target_color)
#         if not p: return False

#         dx = offset_studs_x * self.STUD_PITCH
#         dy = offset_studs_y * self.STUD_PITCH
#         yaw_rad = math.radians(p.yaw)
#         real_offset_x = dx * math.cos(yaw_rad) - dy * math.sin(yaw_rad)
#         real_offset_y = dx * math.sin(yaw_rad) + dy * math.cos(yaw_rad)

#         target_x = p.x + real_offset_x
#         target_y = p.y + real_offset_y

#         self.get_logger().info(f"➡️ [XY 이동] 시각 보정 기반 최적 오프셋 적용")
#         req_xy = GetTargetPose.Request()
#         req_xy.x = target_x; req_xy.y = target_y; req_xy.target_size = "XY"
#         self.call(self.cli_r, req_xy)
#         time.sleep(self.WAIT_TIME) 

#         # 3. Z축 하강 (타겟의 현재 높이 p.z를 기준으로 층수 계산)
#         z_move = (p.z * 1000.0 + self.Z_OFF) - (self.BLOCK_H * layer_index)
        
#         self.call(self.cli_r, GetTargetPose.Request(z=z_move - self.Z_MARGIN, target_size="Z"))
#         time.sleep(self.WAIT_TIME) 
#         self.call(self.cli_r, GetTargetPose.Request(z=self.Z_MARGIN, target_size="Z"))
#         time.sleep(self.WAIT_TIME) 

#         # 4. Open
#         self.call(self.cli_g, SetBool.Request(data=False))
#         time.sleep(self.WAIT_TIME) 
#         self.call(self.cli_r, GetTargetPose.Request(z=-50.0, target_size="Z"))
#         time.sleep(self.WAIT_TIME) 
#         return True

#     def get_best_build_plan(self, current_inventory):
#         recipes = {
#             'big_carrot': {'2x2_yellow': 2, '4x2_yellow': 1, '2x2_blue': 1},
#             'burger': {'4x2_yellow': 2, '4x2_red': 1, '2x2_red': 1}
#         }
#         best_plan = []
#         min_remainder = sum(current_inventory.values())

#         def dfs(inv, current_plan):
#             nonlocal best_plan, min_remainder
#             made_any = False
#             for name, recipe in recipes.items():
#                 can_make = True
#                 for color, count in recipe.items():
#                     if inv.get(color, 0) < count:
#                         can_make = False
#                         break
#                 if can_make:
#                     made_any = True
#                     new_inv = inv.copy()
#                     for color, count in recipe.items():
#                         new_inv[color] -= count
#                     dfs(new_inv, current_plan + [name])
            
#             if not made_any:
#                 remainder = sum(inv.values())
#                 if remainder < min_remainder:
#                     min_remainder = remainder
#                     best_plan = current_plan
#                 elif remainder == min_remainder:
#                     if len(current_plan) > len(best_plan):
#                         best_plan = current_plan

#         dfs(current_inventory, [])
#         return best_plan

#     def build_big_carrot(self):
#         self.get_logger().info("🥕🥕 [큰 당근] 노랑2x2(Pick) -> 노랑2x2(Base) -> 노랑4x2(Pick) -> 파랑2x2(Pick)")
        
#         # 1층
#         if self.pick_target("2x2_yellow"):
#             self.call(self.cli_h, Trigger.Request())
#             if self.visual_insert("2x2_yellow", layer_index=1):
                
#                 # 2층
#                 self.call(self.cli_h, Trigger.Request())
#                 if self.pick_target("4x2_yellow"):
#                     self.call(self.cli_h, Trigger.Request())
#                     if self.visual_insert("2x2_yellow", layer_index=2, yaw_offset=90.0):
                        
#                         # 3층: 베이스(2x2)가 가려졌으므로, 2층의 4x2 노란색을 타겟으로 삼음!
#                         self.call(self.cli_h, Trigger.Request())
#                         if self.pick_target("2x2_blue"):
#                             self.call(self.cli_h, Trigger.Request())
#                             self.visual_insert("4x2_yellow", layer_index=1) # 4x2 위로 1층만 올라가면 됨
#                             self.get_logger().info("✅ 대왕 당근 완성!")

#     def build_burger(self):
#         self.get_logger().info("🍔 [버거] 노랑4x2(Base) -> 빨강4x2(Offset Y -1) -> 빨강2x2(Offset Y +2) -> 노랑4x2(Top)")
        
#         # 1층 - 1번 파트: 빨강 4x2 집기
#         if self.pick_target("4x2_red"):
#             self.call(self.cli_h, Trigger.Request())
#             # 첫 번째 패티는 바닥의 노란색 베이스를 보고 놓음 (-1.0 오프셋)
#             if self.visual_insert("4x2_yellow", layer_index=1, offset_studs_y=-1.0):
                
#                 # 1층 - 2번 파트: 빨강 2x2 집기
#                 self.call(self.cli_h, Trigger.Request())
#                 if self.pick_target("2x2_red"):
#                     self.call(self.cli_h, Trigger.Request())
                    
#                     # 🌟 1단계 업그레이드 완료: 가려진 노란색 대신 방금 놓은 '빨간색 4x2'를 타겟으로!
#                     # -1.0 위치에 있는 빨강 4x2 기준에서 +3.0을 가야 원래 의도한 베이스 기준 +2.0 위치에 도달함.
#                     # 같은 바닥면이므로 layer_index=0, 그리퍼 충돌 방지 90도 꺾기!
#                     if self.visual_insert("4x2_red", layer_index=0, yaw_offset=0.0, offset_studs_y=3.0):
                        
#                         # 2층 - 덮개 노랑 4x2 집기
#                         self.call(self.cli_h, Trigger.Request())
#                         if self.pick_target("4x2_yellow"):
#                             self.call(self.cli_h, Trigger.Request())
                            
#                             # 🌟 2단계 업그레이드 완료: 덮개도 '빨간색 4x2'를 기준으로 삼음!
#                             # -1.0 위치에 있는 빨강 4x2 기준에서 +1.0을 가야 베이스 정중앙(0.0)에 도달함.
#                             # 빨강 4x2 위에 덮으므로 layer_index=1
#                             self.visual_insert("4x2_red", layer_index=1, offset_studs_y=0.0)
#                             self.get_logger().info("✅ 버거 완성!")

#     def run(self):
#         self.get_logger().info("🚀 STARTING VISUAL-STACK ASSEMBLY SEQUENCE (Precision Mode)")
#         self.call(self.cli_h, Trigger.Request())
#         self.call(self.cli_g, SetBool.Request(data=False))
#         time.sleep(1.0) 
        
#         self.get_logger().info("👀 필드 블록 스캔 중...")
#         inventory = {
#             "2x2_yellow": self.count_color("2x2_yellow"),
#             "2x2_blue": self.count_color("2x2_blue"),
#             "2x2_red": self.count_color("2x2_red"),
#             "4x2_yellow": self.count_color("4x2_yellow"),
#             "4x2_red": self.count_color("4x2_red")
#         }
#         self.get_logger().info(f"📦 현재 인벤토리: {inventory}")

#         best_plan = self.get_best_build_plan(inventory)
        
#         if not best_plan:
#             self.get_logger().warn("❌ 조립 가능한 조합이 없습니다.")
#         else:
#             self.get_logger().info(f"🧠 최적 계획: {best_plan}")
#             for item in best_plan:
#                 self.get_logger().info(f"▶️ 작업 시작: {item.upper()}")
#                 if item == 'big_carrot': self.build_big_carrot()
#                 elif item == 'burger': self.build_burger()
                    
#                 self.call(self.cli_h, Trigger.Request())
#                 time.sleep(1.0)

#         self.call(self.cli_h, Trigger.Request())
#         self.get_logger().info("🎉 ALL SEQUENCE DONE")

# def main():
#     rclpy.init()
#     node = MasterNode()
#     node.run()
#     rclpy.shutdown()

# if __name__ == '__main__':
#     main()

import rclpy
from rclpy.node import Node
from srvs_pkg.srv import GetTargetPose
from std_srvs.srv import SetBool, Trigger
import time
import math

class MasterNode(Node):
    def __init__(self):
        super().__init__('master_node')
        self.cli_v = self.create_client(GetTargetPose, '/get_target_pose')
        self.cli_r = self.create_client(GetTargetPose, '/robot_move_step')
        self.cli_g = self.create_client(SetBool, '/control_gripper')
        self.cli_h = self.create_client(Trigger, '/robot_home')
        
        self.Z_OFF = -85.0
        self.Z_MARGIN = 20.0
        self.BLOCK_H = 16.0
        self.WAIT_TIME = 1.5 
        
        self.STUD_PITCH = 0.016 
        self.YAW_TUNE = 0.0  # 필요시 여기서 영점 조절 (예: -1.5)
        
        # 🌟 가장 깨끗하게 인식되었을 때의 타겟 좌표를 기억하는 변수
        self.last_perfect_pose = None 

    def call(self, cli, req):
        while not cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(f'Waiting for {cli.srv_name}...')
        future = cli.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        return future.result()

    def count_color(self, color):
        p = self.call(self.cli_v, GetTargetPose.Request(target_color=f"count_{color}"))
        return int(p.x) if p.success else 0

    def find_target_with_retry(self, color, retries=4):
        for i in range(retries):
            p = self.call(self.cli_v, GetTargetPose.Request(target_color=color))
            if p.success:
                return p
            self.get_logger().warn(f"⚠️ [{color}] 타겟 찾는 중... ({i+1}/{retries})")
            time.sleep(1.0) 
        return None

    def pick_target(self, color):
        self.get_logger().info(f"\n--- PICK TARGET: [{color.upper()}] ---")
        p = self.find_target_with_retry(color)
        if not p: return False
        
        req = GetTargetPose.Request(); req.yaw = p.yaw; req.target_size = "YAW"
        self.call(self.cli_r, req)
        time.sleep(self.WAIT_TIME) 

        p = self.find_target_with_retry(color)
        if not p: return False
        req = GetTargetPose.Request(); req.x = p.x; req.y = p.y; req.target_size = "XY"
        self.call(self.cli_r, req)
        time.sleep(self.WAIT_TIME) 

        p = self.find_target_with_retry(color)
        if not p: return False
        z_move = p.z * 1000.0 + self.Z_OFF
        self.call(self.cli_r, GetTargetPose.Request(z=z_move - self.Z_MARGIN, target_size="Z"))
        time.sleep(self.WAIT_TIME) 
        self.call(self.cli_r, GetTargetPose.Request(z=self.Z_MARGIN, target_size="Z"))
        time.sleep(self.WAIT_TIME) 

        self.call(self.cli_g, SetBool.Request(data=True))
        time.sleep(self.WAIT_TIME) 
        self.call(self.cli_r, GetTargetPose.Request(z=-50.0, target_size="Z"))
        time.sleep(self.WAIT_TIME) 
        return True

    # 🌟 기억된 좌표를 활용하여 눈을 감고 정확히 꽂는 blind_insert 부활
    def blind_insert(self, base_pose, layer_index, yaw_offset=0.0, offset_studs_x=0.0, offset_studs_y=0.0):
        self.get_logger().info(f"\n--- BLIND STACK (메모리 사용): Layer {layer_index} (Y Offset: {offset_studs_y}) ---")
        time.sleep(1.0)

        dx = offset_studs_x * self.STUD_PITCH
        dy = offset_studs_y * self.STUD_PITCH

        yaw_rad = math.radians(base_pose.yaw)
        real_offset_x = dx * math.cos(yaw_rad) - dy * math.sin(yaw_rad)
        real_offset_y = dx * math.sin(yaw_rad) + dy * math.cos(yaw_rad)

        target_x = base_pose.x + real_offset_x
        target_y = base_pose.y + real_offset_y

        req_xy = GetTargetPose.Request()
        req_xy.x = target_x; req_xy.y = target_y; req_xy.target_size = "XY"
        self.call(self.cli_r, req_xy)
        time.sleep(self.WAIT_TIME) 

        target_yaw = base_pose.yaw + yaw_offset + self.YAW_TUNE
        while target_yaw > 90.0: target_yaw -= 180.0
        while target_yaw < -90.0: target_yaw += 180.0

        self.get_logger().info(f"🔄 [YAW 회전] 계산된 고정 각도 회전: {target_yaw:.1f}도")
        req_y = GetTargetPose.Request()
        req_y.yaw = target_yaw; req_y.target_size = "YAW"
        self.call(self.cli_r, req_y)
        time.sleep(self.WAIT_TIME) 

        z_move = (base_pose.z * 1000.0 + self.Z_OFF) - (self.BLOCK_H * layer_index)
        
        self.call(self.cli_r, GetTargetPose.Request(z=z_move - self.Z_MARGIN, target_size="Z"))
        time.sleep(self.WAIT_TIME) 
        self.call(self.cli_r, GetTargetPose.Request(z=self.Z_MARGIN, target_size="Z"))
        time.sleep(self.WAIT_TIME) 

        self.call(self.cli_g, SetBool.Request(data=False))
        time.sleep(self.WAIT_TIME) 
        self.call(self.cli_r, GetTargetPose.Request(z=-50.0, target_size="Z"))
        time.sleep(self.WAIT_TIME) 
        return True

    def visual_insert(self, target_color, layer_index, yaw_offset=0.0, offset_studs_x=0.0, offset_studs_y=0.0):
        self.get_logger().info(f"\n--- VISUAL STACK: [{target_color.upper()}] (Layer +{layer_index}, Y Offset: {offset_studs_y}) ---")
        time.sleep(1.0)

        # 1. 첫 번째 시각 확인: 타겟을 보고 YAW부터 맞춤
        p = self.find_target_with_retry(target_color)
        if not p: return False
        
        target_yaw = p.yaw + yaw_offset + self.YAW_TUNE
        while target_yaw > 90.0: target_yaw -= 180.0
        while target_yaw < -90.0: target_yaw += 180.0

        self.get_logger().info(f"🔄 [YAW 회전] 시각 보정 기반 회전: {target_yaw:.1f}도")
        req_y = GetTargetPose.Request()
        req_y.yaw = target_yaw; req_y.target_size = "YAW"
        self.call(self.cli_r, req_y)
        time.sleep(self.WAIT_TIME)

        # 2. 두 번째 시각 확인: YAW가 정렬된 상태에서 카메라로 정확한 XY 재추출
        p = self.find_target_with_retry(target_color)
        if not p: return False

        # 🌟 타겟을 성공적으로 찾았다면 이 완벽한 좌표를 기억해둠!
        self.last_perfect_pose = p

        dx = offset_studs_x * self.STUD_PITCH
        dy = offset_studs_y * self.STUD_PITCH
        yaw_rad = math.radians(p.yaw)
        real_offset_x = dx * math.cos(yaw_rad) - dy * math.sin(yaw_rad)
        real_offset_y = dx * math.sin(yaw_rad) + dy * math.cos(yaw_rad)

        target_x = p.x + real_offset_x
        target_y = p.y + real_offset_y

        self.get_logger().info(f"➡️ [XY 이동] 시각 보정 기반 최적 오프셋 적용")
        req_xy = GetTargetPose.Request()
        req_xy.x = target_x; req_xy.y = target_y; req_xy.target_size = "XY"
        self.call(self.cli_r, req_xy)
        time.sleep(self.WAIT_TIME) 

        # 3. Z축 하강 (타겟의 현재 높이 p.z를 기준으로 층수 계산)
        z_move = (p.z * 1000.0 + self.Z_OFF) - (self.BLOCK_H * layer_index)
        
        self.call(self.cli_r, GetTargetPose.Request(z=z_move - self.Z_MARGIN, target_size="Z"))
        time.sleep(self.WAIT_TIME) 
        self.call(self.cli_r, GetTargetPose.Request(z=self.Z_MARGIN, target_size="Z"))
        time.sleep(self.WAIT_TIME) 

        # 4. Open
        self.call(self.cli_g, SetBool.Request(data=False))
        time.sleep(self.WAIT_TIME) 
        self.call(self.cli_r, GetTargetPose.Request(z=-50.0, target_size="Z"))
        time.sleep(self.WAIT_TIME) 
        return True

    def get_best_build_plan(self, current_inventory):
        recipes = {
            'big_carrot': {'2x2_yellow': 2, '4x2_yellow': 1, '2x2_blue': 1},
            'burger': {'4x2_yellow': 2, '4x2_red': 1, '2x2_red': 1}
        }
        best_plan = []
        min_remainder = sum(current_inventory.values())

        def dfs(inv, current_plan):
            nonlocal best_plan, min_remainder
            made_any = False
            for name, recipe in recipes.items():
                can_make = True
                for color, count in recipe.items():
                    if inv.get(color, 0) < count:
                        can_make = False
                        break
                if can_make:
                    made_any = True
                    new_inv = inv.copy()
                    for color, count in recipe.items():
                        new_inv[color] -= count
                    dfs(new_inv, current_plan + [name])
            
            if not made_any:
                remainder = sum(inv.values())
                if remainder < min_remainder:
                    min_remainder = remainder
                    best_plan = current_plan
                elif remainder == min_remainder:
                    if len(current_plan) > len(best_plan):
                        best_plan = current_plan

        dfs(current_inventory, [])
        return best_plan

    def build_big_carrot(self):
        self.get_logger().info("🥕🥕 [큰 당근] 노랑2x2(Pick) -> 노랑2x2(Base) -> 노랑4x2(Pick) -> 파랑2x2(Pick)")
        
        # 1층
        if self.pick_target("2x2_yellow"):
            self.call(self.cli_h, Trigger.Request())
            if self.visual_insert("2x2_yellow", layer_index=1):
                
                # 2층
                self.call(self.cli_h, Trigger.Request())
                if self.pick_target("4x2_yellow"):
                    self.call(self.cli_h, Trigger.Request())
                    if self.visual_insert("2x2_yellow", layer_index=2, yaw_offset=90.0):
                        
                        # 3층
                        self.call(self.cli_h, Trigger.Request())
                        if self.pick_target("2x2_blue"):
                            self.call(self.cli_h, Trigger.Request())
                            self.visual_insert("4x2_yellow", layer_index=1) 
                            self.get_logger().info("✅ 대왕 당근 완성!")

    def build_burger(self):
        self.get_logger().info("🍔 [버거] 노랑4x2(Base) -> 빨강4x2(Offset Y -1) -> 빨강2x2(Offset Y +2) -> 노랑4x2(Top)")
        
        # 1층 - 1번 파트: 빨강 4x2 집기
        if self.pick_target("4x2_red"):
            self.call(self.cli_h, Trigger.Request())
            # 첫 번째 패티는 바닥의 노란색 베이스를 보고 놓음 (-1.0 오프셋)
            if self.visual_insert("4x2_yellow", layer_index=1, offset_studs_y=-1.0):
                
                # 1층 - 2번 파트: 빨강 2x2 집기
                self.call(self.cli_h, Trigger.Request())
                if self.pick_target("2x2_red"):
                    self.call(self.cli_h, Trigger.Request())
                    
                    # 방금 놓은 '빨간색 4x2'를 타겟으로! (이때 self.last_perfect_pose에 완벽한 좌표가 저장됨)
                    if self.visual_insert("4x2_red", layer_index=0, yaw_offset=0.0, offset_studs_y=3.0):
                        
                        # 2층 - 덮개 노랑 4x2 집기
                        self.call(self.cli_h, Trigger.Request())
                        if self.pick_target("4x2_yellow"):
                            self.call(self.cli_h, Trigger.Request())
                            
                            # 🌟 비전 튐 방지: 저장해둔 완벽한 빨간색 4x2 좌표를 꺼내서 눈 감고 꽂음!
                            # 빨강 4x2 기준에서 +1.0 오프셋을 주면 베이스 정중앙에 딱 맞음.
                            if self.last_perfect_pose:
                                self.get_logger().info("🧠 [메모리 사용] 덩어리 인식 오류 방지: 저장된 좌표로 덮개 조립!")
                                self.blind_insert(self.last_perfect_pose, layer_index=1, offset_studs_y=1.0)
                                self.get_logger().info("✅ 버거 완성!")
                            else:
                                self.get_logger().warn("❌ 저장된 좌표가 없습니다. 조립 실패.")

    def run(self):
        self.get_logger().info("🚀 STARTING VISUAL-STACK ASSEMBLY SEQUENCE (Precision Mode)")
        self.call(self.cli_h, Trigger.Request())
        self.call(self.cli_g, SetBool.Request(data=False))
        time.sleep(1.0) 
        
        self.get_logger().info("👀 필드 블록 스캔 중...")
        inventory = {
            "2x2_yellow": self.count_color("2x2_yellow"),
            "2x2_blue": self.count_color("2x2_blue"),
            "2x2_red": self.count_color("2x2_red"),
            "4x2_yellow": self.count_color("4x2_yellow"),
            "4x2_red": self.count_color("4x2_red")
        }
        self.get_logger().info(f"📦 현재 인벤토리: {inventory}")

        best_plan = self.get_best_build_plan(inventory)
        
        if not best_plan:
            self.get_logger().warn("❌ 조립 가능한 조합이 없습니다.")
        else:
            self.get_logger().info(f"🧠 최적 계획: {best_plan}")
            for item in best_plan:
                self.get_logger().info(f"▶️ 작업 시작: {item.upper()}")
                if item == 'big_carrot': self.build_big_carrot()
                elif item == 'burger': self.build_burger()
                    
                self.call(self.cli_h, Trigger.Request())
                time.sleep(1.0)

        self.call(self.cli_h, Trigger.Request())
        self.get_logger().info("🎉 ALL SEQUENCE DONE")

def main():
    rclpy.init()
    node = MasterNode()
    node.run()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

# import rclpy
# from rclpy.node import Node
# from srvs_pkg.srv import GetTargetPose
# from std_srvs.srv import SetBool, Trigger
# import time
# import math

# class MasterNode(Node):
#     def __init__(self):
#         super().__init__('master_node')
#         self.cli_v = self.create_client(GetTargetPose, '/get_target_pose')
#         self.cli_r = self.create_client(GetTargetPose, '/robot_move_step')
#         self.cli_g = self.create_client(SetBool, '/control_gripper')
#         self.cli_h = self.create_client(Trigger, '/robot_home')
        
#         self.Z_OFF = -85.0
#         self.Z_MARGIN = 20.0
#         self.BLOCK_H = 16.0
#         self.WAIT_TIME = 1.5 
        
#         self.STUD_PITCH = 0.016 
#         self.YAW_TUNE = 0.0  # 필요시 여기서 영점 조절 (예: -1.5)
        
#         # 🌟 가장 깨끗하게 인식되었을 때의 타겟 좌표를 기억하는 변수
#         self.last_perfect_pose = None 

#     def call(self, cli, req):
#         while not cli.wait_for_service(timeout_sec=1.0):
#             self.get_logger().info(f'Waiting for {cli.srv_name}...')
#         future = cli.call_async(req)
#         rclpy.spin_until_future_complete(self, future)
#         return future.result()

#     def count_color(self, color):
#         p = self.call(self.cli_v, GetTargetPose.Request(target_color=f"count_{color}"))
#         return int(p.x) if p.success else 0

#     def find_target_with_retry(self, color, retries=4):
#         for i in range(retries):
#             p = self.call(self.cli_v, GetTargetPose.Request(target_color=color))
#             if p.success:
#                 return p
#             self.get_logger().warn(f"⚠️ [{color}] 타겟 찾는 중... ({i+1}/{retries})")
#             time.sleep(1.0) 
#         return None

#     def pick_target(self, color):
#         self.get_logger().info(f"\n--- PICK TARGET: [{color.upper()}] ---")
#         p = self.find_target_with_retry(color)
#         if not p: return False
        
#         req = GetTargetPose.Request(); req.yaw = p.yaw; req.target_size = "YAW"
#         self.call(self.cli_r, req)
#         time.sleep(self.WAIT_TIME) 

#         p = self.find_target_with_retry(color)
#         if not p: return False
#         req = GetTargetPose.Request(); req.x = p.x; req.y = p.y; req.target_size = "XY"
#         self.call(self.cli_r, req)
#         time.sleep(self.WAIT_TIME) 

#         p = self.find_target_with_retry(color)
#         if not p: return False
#         z_move = p.z * 1000.0 + self.Z_OFF
#         self.call(self.cli_r, GetTargetPose.Request(z=z_move - self.Z_MARGIN, target_size="Z"))
#         time.sleep(self.WAIT_TIME) 
#         self.call(self.cli_r, GetTargetPose.Request(z=self.Z_MARGIN, target_size="Z"))
#         time.sleep(self.WAIT_TIME) 

#         self.call(self.cli_g, SetBool.Request(data=True))
#         time.sleep(self.WAIT_TIME) 
#         self.call(self.cli_r, GetTargetPose.Request(z=-50.0, target_size="Z"))
#         time.sleep(self.WAIT_TIME) 
#         return True

#     # 🌟 기억된 좌표를 활용하여 눈을 감고 정확히 꽂는 blind_insert
#     def blind_insert(self, base_pose, layer_index, yaw_offset=0.0, offset_studs_x=0.0, offset_studs_y=0.0):
#         self.get_logger().info(f"\n--- BLIND STACK (메모리 사용): Layer {layer_index} (Y Offset: {offset_studs_y}) ---")
#         time.sleep(1.0)

#         dx = offset_studs_x * self.STUD_PITCH
#         dy = offset_studs_y * self.STUD_PITCH

#         yaw_rad = math.radians(base_pose.yaw)
#         real_offset_x = dx * math.cos(yaw_rad) - dy * math.sin(yaw_rad)
#         real_offset_y = dx * math.sin(yaw_rad) + dy * math.cos(yaw_rad)

#         target_x = base_pose.x + real_offset_x
#         target_y = base_pose.y + real_offset_y

#         req_xy = GetTargetPose.Request()
#         req_xy.x = target_x; req_xy.y = target_y; req_xy.target_size = "XY"
#         self.call(self.cli_r, req_xy)
#         time.sleep(self.WAIT_TIME) 

#         target_yaw = base_pose.yaw + yaw_offset + self.YAW_TUNE
#         while target_yaw > 90.0: target_yaw -= 180.0
#         while target_yaw < -90.0: target_yaw += 180.0

#         self.get_logger().info(f"🔄 [YAW 회전] 계산된 고정 각도 회전: {target_yaw:.1f}도")
#         req_y = GetTargetPose.Request()
#         req_y.yaw = target_yaw; req_y.target_size = "YAW"
#         self.call(self.cli_r, req_y)
#         time.sleep(self.WAIT_TIME) 

#         z_move = (base_pose.z * 1000.0 + self.Z_OFF) - (self.BLOCK_H * layer_index)
        
#         self.call(self.cli_r, GetTargetPose.Request(z=z_move - self.Z_MARGIN, target_size="Z"))
#         time.sleep(self.WAIT_TIME) 
#         self.call(self.cli_r, GetTargetPose.Request(z=self.Z_MARGIN, target_size="Z"))
#         time.sleep(self.WAIT_TIME) 

#         self.call(self.cli_g, SetBool.Request(data=False))
#         time.sleep(self.WAIT_TIME) 
#         self.call(self.cli_r, GetTargetPose.Request(z=-50.0, target_size="Z"))
#         time.sleep(self.WAIT_TIME) 
#         return True

#     def visual_insert(self, target_color, layer_index, yaw_offset=0.0, offset_studs_x=0.0, offset_studs_y=0.0):
#         self.get_logger().info(f"\n--- VISUAL STACK: [{target_color.upper()}] (Layer +{layer_index}, Y Offset: {offset_studs_y}) ---")
#         time.sleep(1.0)

#         # 1. 첫 번째 시각 확인: (카메라가 돌아가기 전 진짜 월드 각도 측정)
#         p1 = self.find_target_with_retry(target_color)
#         if not p1: return False
        
#         target_yaw = p1.yaw + yaw_offset + self.YAW_TUNE
#         while target_yaw > 90.0: target_yaw -= 180.0
#         while target_yaw < -90.0: target_yaw += 180.0

#         self.get_logger().info(f"🔄 [YAW 회전] 시각 보정 기반 회전: {target_yaw:.1f}도")
#         req_y = GetTargetPose.Request()
#         req_y.yaw = target_yaw; req_y.target_size = "YAW"
#         self.call(self.cli_r, req_y)
#         time.sleep(self.WAIT_TIME)

#         # 2. 두 번째 시각 확인: (손목이 돌아간 후 정밀한 X, Y 측정)
#         p2 = self.find_target_with_retry(target_color)
#         if not p2: return False

#         # 🌟 핵심 해결책: p2의 0도가 된 가짜 Yaw를 p1의 진짜 Yaw로 덮어쓰기!
#         p2.yaw = p1.yaw
        
#         # 이제 완벽한 하이브리드 좌표(정밀 XY + 진짜 Yaw)를 기억 상자에 저장!
#         self.last_perfect_pose = p2

#         dx = offset_studs_x * self.STUD_PITCH
#         dy = offset_studs_y * self.STUD_PITCH
#         yaw_rad = math.radians(p1.yaw)
#         real_offset_x = dx * math.cos(yaw_rad) - dy * math.sin(yaw_rad)
#         real_offset_y = dx * math.sin(yaw_rad) + dy * math.cos(yaw_rad)

#         target_x = p2.x + real_offset_x
#         target_y = p2.y + real_offset_y

#         self.get_logger().info(f"➡️ [XY 이동] 시각 보정 기반 최적 오프셋 적용")
#         req_xy = GetTargetPose.Request()
#         req_xy.x = target_x; req_xy.y = target_y; req_xy.target_size = "XY"
#         self.call(self.cli_r, req_xy)
#         time.sleep(self.WAIT_TIME) 

#         # 3. Z축 하강 (타겟의 현재 높이 p2.z를 기준으로 층수 계산)
#         z_move = (p2.z * 1000.0 + self.Z_OFF) - (self.BLOCK_H * layer_index)
        
#         self.call(self.cli_r, GetTargetPose.Request(z=z_move - self.Z_MARGIN, target_size="Z"))
#         time.sleep(self.WAIT_TIME) 
#         self.call(self.cli_r, GetTargetPose.Request(z=self.Z_MARGIN, target_size="Z"))
#         time.sleep(self.WAIT_TIME) 

#         # 4. Open
#         self.call(self.cli_g, SetBool.Request(data=False))
#         time.sleep(self.WAIT_TIME) 
#         self.call(self.cli_r, GetTargetPose.Request(z=-50.0, target_size="Z"))
#         time.sleep(self.WAIT_TIME) 
#         return True

#     def get_best_build_plan(self, current_inventory):
#         recipes = {
#             'big_carrot': {'2x2_yellow': 2, '4x2_yellow': 1, '2x2_blue': 1},
#             'burger': {'4x2_yellow': 2, '4x2_red': 1, '2x2_red': 1}
#         }
#         best_plan = []
#         min_remainder = sum(current_inventory.values())

#         def dfs(inv, current_plan):
#             nonlocal best_plan, min_remainder
#             made_any = False
#             for name, recipe in recipes.items():
#                 can_make = True
#                 for color, count in recipe.items():
#                     if inv.get(color, 0) < count:
#                         can_make = False
#                         break
#                 if can_make:
#                     made_any = True
#                     new_inv = inv.copy()
#                     for color, count in recipe.items():
#                         new_inv[color] -= count
#                     dfs(new_inv, current_plan + [name])
            
#             if not made_any:
#                 remainder = sum(inv.values())
#                 if remainder < min_remainder:
#                     min_remainder = remainder
#                     best_plan = current_plan
#                 elif remainder == min_remainder:
#                     if len(current_plan) > len(best_plan):
#                         best_plan = current_plan

#         dfs(current_inventory, [])
#         return best_plan

#     def build_big_carrot(self):
#         self.get_logger().info("🥕🥕 [큰 당근] 노랑2x2(Pick) -> 노랑2x2(Base) -> 노랑4x2(Pick) -> 파랑2x2(Pick)")
        
#         # 1층
#         if self.pick_target("2x2_yellow"):
#             self.call(self.cli_h, Trigger.Request())
#             if self.visual_insert("2x2_yellow", layer_index=1):
                
#                 # 2층
#                 self.call(self.cli_h, Trigger.Request())
#                 if self.pick_target("4x2_yellow"):
#                     self.call(self.cli_h, Trigger.Request())
#                     if self.visual_insert("2x2_yellow", layer_index=2, yaw_offset=90.0):
                        
#                         # 3층: 베이스(2x2)가 가려졌으므로, 2층의 4x2 노란색을 타겟으로 삼음!
#                         self.call(self.cli_h, Trigger.Request())
#                         if self.pick_target("2x2_blue"):
#                             self.call(self.cli_h, Trigger.Request())
#                             self.visual_insert("4x2_yellow", layer_index=1) 
#                             self.get_logger().info("✅ 대왕 당근 완성!")

#     def build_burger(self):
#         self.get_logger().info("🍔 [버거] 노랑4x2(Base) -> 빨강4x2(Offset Y -1) -> 빨강2x2(Offset Y +2) -> 노랑4x2(Top)")
        
#         # 1층 - 1번 파트: 빨강 4x2 집기
#         if self.pick_target("4x2_red"):
#             self.call(self.cli_h, Trigger.Request())
#             # 첫 번째 패티는 바닥의 노란색 베이스를 보고 놓음 (-1.0 오프셋)
#             if self.visual_insert("4x2_yellow", layer_index=1, offset_studs_y=-1.0):
                
#                 # 1층 - 2번 파트: 빨강 2x2 집기
#                 self.call(self.cli_h, Trigger.Request())
#                 if self.pick_target("2x2_red"):
#                     self.call(self.cli_h, Trigger.Request())
                    
#                     # 방금 놓은 '빨간색 4x2'를 타겟으로! (이때 self.last_perfect_pose에 완벽한 좌표가 저장됨)
#                     if self.visual_insert("4x2_red", layer_index=0, yaw_offset=0.0, offset_studs_y=3.0):
                        
#                         # 2층 - 덮개 노랑 4x2 집기
#                         self.call(self.cli_h, Trigger.Request())
#                         if self.pick_target("4x2_yellow"):
#                             self.call(self.cli_h, Trigger.Request())
                            
#                             # 🌟 비전 튐 방지 + 상대각도 초기화 방어: 저장된 하이브리드 좌표로 덮개 덮기!
#                             if self.last_perfect_pose:
#                                 self.get_logger().info("🧠 [메모리 사용] 덩어리 인식 오류 방지: 저장된 좌표로 덮개 조립!")
#                                 self.blind_insert(self.last_perfect_pose, layer_index=1, offset_studs_y=1.0)
#                                 self.get_logger().info("✅ 버거 완성!")
#                             else:
#                                 self.get_logger().warn("❌ 저장된 좌표가 없습니다. 조립 실패.")

#     def run(self):
#         self.get_logger().info("🚀 STARTING VISUAL-STACK ASSEMBLY SEQUENCE (Precision Mode)")
#         self.call(self.cli_h, Trigger.Request())
#         self.call(self.cli_g, SetBool.Request(data=False))
#         time.sleep(1.0) 
        
#         self.get_logger().info("👀 필드 블록 스캔 중...")
#         inventory = {
#             "2x2_yellow": self.count_color("2x2_yellow"),
#             "2x2_blue": self.count_color("2x2_blue"),
#             "2x2_red": self.count_color("2x2_red"),
#             "4x2_yellow": self.count_color("4x2_yellow"),
#             "4x2_red": self.count_color("4x2_red")
#         }
#         self.get_logger().info(f"📦 현재 인벤토리: {inventory}")

#         best_plan = self.get_best_build_plan(inventory)
        
#         if not best_plan:
#             self.get_logger().warn("❌ 조립 가능한 조합이 없습니다.")
#         else:
#             self.get_logger().info(f"🧠 최적 계획: {best_plan}")
#             for item in best_plan:
#                 self.get_logger().info(f"▶️ 작업 시작: {item.upper()}")
#                 if item == 'big_carrot': self.build_big_carrot()
#                 elif item == 'burger': self.build_burger()
                    
#                 self.call(self.cli_h, Trigger.Request())
#                 time.sleep(1.0)

#         self.call(self.cli_h, Trigger.Request())
#         self.get_logger().info("🎉 ALL SEQUENCE DONE")

# def main():
#     rclpy.init()
#     node = MasterNode()
#     node.run()
#     rclpy.shutdown()

# if __name__ == '__main__':
#     main()