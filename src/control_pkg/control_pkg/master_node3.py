# # # import rclpy
# # # from rclpy.node import Node
# # # from srvs_pkg.srv import GetTargetPose
# # # from std_srvs.srv import SetBool, Trigger
# # # import time

# # # class MasterNode(Node):
# # #     def __init__(self):
# # #         super().__init__('master_node')
# # #         self.cli_v = self.create_client(GetTargetPose, '/get_target_pose')
# # #         self.cli_r = self.create_client(GetTargetPose, '/robot_move_step')
# # #         self.cli_g = self.create_client(SetBool, '/control_gripper')
# # #         self.cli_h = self.create_client(Trigger, '/robot_home')
        
# # #         self.Z_OFF = -85.0
# # #         self.Z_MARGIN = 20.0
# # #         self.BLOCK_H = 16.0
# # #         self.WAIT_TIME = 1.5 

# # #     def call(self, cli, req):
# # #         while not cli.wait_for_service(timeout_sec=1.0):
# # #             self.get_logger().info(f'Waiting for {cli.srv_name}...')
# # #         future = cli.call_async(req)
# # #         rclpy.spin_until_future_complete(self, future)
# # #         return future.result()

# # #     # 🌟 비전 노드에 "count_색상"을 요청하여 개수를 파악하는 함수
# # #     def count_color(self, color):
# # #         p = self.call(self.cli_v, GetTargetPose.Request(target_color=f"count_{color}"))
# # #         return int(p.x) if p.success else 0

# # #     def find_target_with_retry(self, color, retries=4):
# # #         for i in range(retries):
# # #             p = self.call(self.cli_v, GetTargetPose.Request(target_color=color))
# # #             if p.success:
# # #                 return p
# # #             self.get_logger().warn(f"⚠️ [{color}] 찾는 중... 대기 ({i+1}/{retries})")
# # #             time.sleep(1.0) 
# # #         return None

# # #     def pick_target(self, color):
# # #         self.get_logger().info(f"\n--- PICK TARGET: [{color.upper()}] ---")
# # #         p = self.find_target_with_retry(color)
# # #         if not p: return False
# # #         req = GetTargetPose.Request(); req.yaw = p.yaw; req.target_size = "YAW"
# # #         self.call(self.cli_r, req)
# # #         time.sleep(self.WAIT_TIME) 

# # #         p = self.find_target_with_retry(color)
# # #         if not p: return False
# # #         req = GetTargetPose.Request(); req.x = p.x; req.y = p.y; req.target_size = "XY"
# # #         self.call(self.cli_r, req)
# # #         time.sleep(self.WAIT_TIME) 

# # #         p = self.find_target_with_retry(color)
# # #         if not p: return False
# # #         z_move = p.z * 1000.0 + self.Z_OFF
# # #         self.call(self.cli_r, GetTargetPose.Request(z=z_move - self.Z_MARGIN, target_size="Z"))
# # #         time.sleep(self.WAIT_TIME) 
# # #         self.call(self.cli_r, GetTargetPose.Request(z=self.Z_MARGIN, target_size="Z"))
# # #         time.sleep(self.WAIT_TIME) 

# # #         self.call(self.cli_g, SetBool.Request(data=True))
# # #         time.sleep(self.WAIT_TIME) 
# # #         self.call(self.cli_r, GetTargetPose.Request(z=-50.0, target_size="Z"))
# # #         time.sleep(self.WAIT_TIME) 
# # #         return True

# # #     def insert_to_target(self, color, yaw_offset=0.0):
# # #         self.get_logger().info(f"\n--- STACK ON: [{color.upper()}] (Yaw Offset: +{yaw_offset}도) ---")
# # #         time.sleep(1.0)

# # #         # 1. YAW
# # #         p = self.find_target_with_retry(color, retries=5)
# # #         if not p: return False
# # #         req_y = GetTargetPose.Request()
# # #         req_y.yaw = p.yaw + yaw_offset 
# # #         req_y.target_size = "YAW"
# # #         self.call(self.cli_r, req_y)
# # #         time.sleep(self.WAIT_TIME) 
        
# # #         # 2. XY
# # #         p = self.find_target_with_retry(color)
# # #         if not p: return False
# # #         req_xy = GetTargetPose.Request(); req_xy.x = p.x; req_xy.y = p.y; req_xy.target_size = "XY"
# # #         self.call(self.cli_r, req_xy)
# # #         time.sleep(self.WAIT_TIME) 

# # #         # 3. Z
# # #         p = self.find_target_with_retry(color)
# # #         if not p: return False
# # #         z_move = (p.z * 1000.0 + self.Z_OFF) - self.BLOCK_H
# # #         self.call(self.cli_r, GetTargetPose.Request(z=z_move - self.Z_MARGIN, target_size="Z"))
# # #         time.sleep(self.WAIT_TIME) 
# # #         self.call(self.cli_r, GetTargetPose.Request(z=self.Z_MARGIN, target_size="Z"))
# # #         time.sleep(self.WAIT_TIME) 

# # #         # 4. Open
# # #         self.call(self.cli_g, SetBool.Request(data=False))
# # #         time.sleep(self.WAIT_TIME) 
# # #         self.call(self.cli_r, GetTargetPose.Request(z=-50.0, target_size="Z"))
# # #         time.sleep(self.WAIT_TIME) 
# # #         return True

# # #     # =========================================================
# # #     # 🧠 최적화 알고리즘: 남는 블록이 가장 적은 조립 계획 찾기
# # #     # =========================================================
# # #     def get_best_build_plan(self, current_inventory):
# # #         recipes = {
# # #             'battery': {'2x2_yellow': 1, '2x2_blue': 1},
# # #             'magnet': {'2x2_blue': 1, '2x2_red': 1},
# # #             'e_stop': {'2x2_red': 1, '4x2_yellow': 1},
# # #             'carrot': {'2x2_green': 1, '2x2_yellow': 2},
# # #             'traffic_light': {'2x2_red': 1, '2x2_yellow': 1, '2x2_green': 1},
# # #             'small_tree': {'2x2_red': 1, '4x2_red': 1, '2x2_yellow': 1},
# # #             'hammer': {'4x2_blue': 1, '2x2_red': 2}
# # #         }

# # #         best_plan = []
# # #         min_remainder = sum(current_inventory.values())

# # #         def dfs(inv, current_plan):
# # #             nonlocal best_plan, min_remainder
            
# # #             made_any = False
# # #             for name, recipe in recipes.items():
# # #                 # 해당 레시피를 만들 수 있는지 확인
# # #                 can_make = True
# # #                 for color, count in recipe.items():
# # #                     if inv.get(color, 0) < count:
# # #                         can_make = False
# # #                         break
                
# # #                 # 만들 수 있다면 블록 차감 후 재귀 탐색
# # #                 if can_make:
# # #                     made_any = True
# # #                     new_inv = inv.copy()
# # #                     for color, count in recipe.items():
# # #                         new_inv[color] -= count
# # #                     dfs(new_inv, current_plan + [name])
            
# # #             # 더 이상 만들 수 있는 조합이 없을 때 최적의 계획 갱신
# # #             if not made_any:
# # #                 remainder = sum(inv.values())
# # #                 if remainder < min_remainder:
# # #                     min_remainder = remainder
# # #                     best_plan = current_plan
# # #                 # 남는 블록 수가 같다면 더 많은 개수를 조립하는 계획을 우선
# # #                 elif remainder == min_remainder:
# # #                     if len(current_plan) > len(best_plan):
# # #                         best_plan = current_plan

# # #         dfs(current_inventory, [])
# # #         return best_plan

# # #     # =========================================================
# # #     # 2단 조합 (배터리, 자석, 비상정지)
# # #     # =========================================================
# # #     def build_battery(self):
# # #         self.get_logger().info("🔋 [배터리 조립]: 노란색(2x2) -> 파란색(2x2)")
# # #         if self.pick_target("2x2_yellow"):
# # #             self.call(self.cli_h, Trigger.Request())
# # #             if self.insert_to_target("2x2_blue"):
# # #                 self.get_logger().info("✅ 배터리 조립 완료!")
# # #             else:
# # #                 self.get_logger().error("❌ 파란색 스택 실패!")
# # #         else:
# # #             self.get_logger().error("❌ 노란색 픽업 실패!")

# # #     def build_magnet(self):
# # #         self.get_logger().info("🧲 [자석 조립]: 파란색(2x2) -> 빨간색(2x2)")
# # #         if self.pick_target("2x2_blue"):
# # #             self.call(self.cli_h, Trigger.Request())
# # #             if self.insert_to_target("2x2_red"):
# # #                 self.get_logger().info("✅ 자석 조립 완료!")
# # #             else:
# # #                 self.get_logger().error("❌ 빨간색 스택 실패!")
# # #         else:
# # #             self.get_logger().error("❌ 파란색 픽업 실패!")

# # #     def build_e_stop(self):
# # #         self.get_logger().info("🛑 [비상정지 조립]: 빨간색(2x2) -> 노란색(4x2)")
# # #         if self.pick_target("2x2_red"):
# # #             self.call(self.cli_h, Trigger.Request())
# # #             # 비상정지는 십자 모양이므로 yaw_offset = -90.0
# # #             if self.insert_to_target("4x2_yellow", yaw_offset=-90.0):
# # #                 self.get_logger().info("✅ 비상정지 조립 완료!")
# # #             else:
# # #                 self.get_logger().error("❌ 노란색 4x2 스택 실패!")
# # #         else:
# # #             self.get_logger().error("❌ 빨간색 픽업 실패!")

# # #     # =========================================================
# # #     # 3단 조합 (당근, 신호등, 작은나무, 망치)
# # #     # =========================================================
# # #     def build_carrot(self):
# # #         self.get_logger().info("🥕 [당근 조립]: 초록(2x2) + 노랑(2x2) + 노랑(2x2)")
# # #         if self.pick_target("2x2_yellow"):
# # #             self.call(self.cli_h, Trigger.Request())
# # #             if self.insert_to_target("2x2_yellow"):
# # #                 self.call(self.cli_h, Trigger.Request())
# # #                 if self.pick_target("2x2_green"):
# # #                     self.call(self.cli_h, Trigger.Request())
# # #                     if self.insert_to_target("2x2_yellow"):
# # #                         self.get_logger().info("✅ 당근 완성!")
# # #         else:
# # #             self.get_logger().error("❌ 당근 조립 중단: 픽업/스택 실패")

# # #     def build_traffic_light(self):
# # #         self.get_logger().info("🚦 [신호등 조립]: 빨강(2x2) + 노랑(2x2) + 초록(2x2)")
# # #         if self.pick_target("2x2_yellow"):
# # #             self.call(self.cli_h, Trigger.Request())
# # #             if self.insert_to_target("2x2_green"):
# # #                 self.call(self.cli_h, Trigger.Request())
# # #                 if self.pick_target("2x2_red"):
# # #                     self.call(self.cli_h, Trigger.Request())
# # #                     if self.insert_to_target("2x2_yellow"):
# # #                         self.get_logger().info("✅ 신호등 완성!")
# # #         else:
# # #             self.get_logger().error("❌ 신호등 조립 중단: 픽업/스택 실패")

# # #     def build_small_tree(self):
# # #         self.get_logger().info("🌳 [작은 나무 조립]: 빨강(4x2) + 노랑(2x2) + 빨강(2x2)")
# # #         if self.pick_target("4x2_red"):
# # #             self.call(self.cli_h, Trigger.Request())
# # #             if self.insert_to_target("2x2_yellow"):
# # #                 self.call(self.cli_h, Trigger.Request())
# # #                 if self.pick_target("2x2_red"):
# # #                     self.call(self.cli_h, Trigger.Request())
# # #                     if self.insert_to_target("4x2_red"):
# # #                         self.get_logger().info("✅ 작은 나무 완성!")
# # #         else:
# # #             self.get_logger().error("❌ 작은 나무 조립 중단: 픽업/스택 실패")

# # #     def build_hammer(self):
# # #         self.get_logger().info("🔨 [망치 조립]: 파랑(4x2) + 빨강(2x2) + 빨강(2x2)")
# # #         if self.pick_target("2x2_red"):
# # #             self.call(self.cli_h, Trigger.Request())
# # #             if self.insert_to_target("2x2_red"):
# # #                 self.call(self.cli_h, Trigger.Request())
# # #                 if self.pick_target("4x2_blue"):
# # #                     self.call(self.cli_h, Trigger.Request())
# # #                     # 망치 머리는 90도 회전
# # #                     if self.insert_to_target("2x2_red", yaw_offset=90.0):
# # #                         self.get_logger().info("✅ 망치 완성!")
# # #         else:
# # #             self.get_logger().error("❌ 망치 조립 중단: 픽업/스택 실패")

# # #     # =========================================================
# # #     # 메인 제어 루프
# # #     # =========================================================
# # #     def run(self):
# # #         self.get_logger().info("🚀 STARTING AI OPTIMIZED ASSEMBLY SEQUENCE")
        
# # #         self.call(self.cli_h, Trigger.Request())
# # #         self.call(self.cli_g, SetBool.Request(data=False))
# # #         time.sleep(1.0) 
        
# # #         # 1. 필드 스캔
# # #         self.get_logger().info("👀 필드 블록 스캔 중...")
# # #         inventory = {
# # #             "2x2_yellow": self.count_color("2x2_yellow"),
# # #             "2x2_blue": self.count_color("2x2_blue"),
# # #             "2x2_red": self.count_color("2x2_red"),
# # #             "2x2_green": self.count_color("2x2_green"),
# # #             "4x2_yellow": self.count_color("4x2_yellow"),
# # #             "4x2_red": self.count_color("4x2_red"),
# # #             "4x2_blue": self.count_color("4x2_blue")
# # #         }
# # #         self.get_logger().info(f"📦 현재 인벤토리: {inventory}")

# # #         # 2. 최적의 조립 계획 도출
# # #         best_plan = self.get_best_build_plan(inventory)
        
# # #         if not best_plan:
# # #             self.get_logger().warn("❌ 현재 필드의 블록으로는 어떤 조합도 만들 수 없습니다.")
# # #         else:
# # #             self.get_logger().info(f"🧠 최적의 계획을 찾았습니다! 실행 순서: {best_plan}")
            
# # #             # 3. 계획에 따라 순차적으로 실행
# # #             for item in best_plan:
# # #                 self.get_logger().info(f"▶️ 다음 작업 시작: {item.upper()}")
                
# # #                 if item == 'battery':
# # #                     self.build_battery()
# # #                 elif item == 'magnet':
# # #                     self.build_magnet()
# # #                 elif item == 'e_stop':
# # #                     self.build_e_stop()
# # #                 elif item == 'carrot':
# # #                     self.build_carrot()
# # #                 elif item == 'traffic_light':
# # #                     self.build_traffic_light()
# # #                 elif item == 'small_tree':
# # #                     self.build_small_tree()
# # #                 elif item == 'hammer':
# # #                     self.build_hammer()
                    
# # #                 # 하나의 조합 조립이 끝날 때마다 로봇 홈 위치로 복귀 및 1초 대기
# # #                 self.call(self.cli_h, Trigger.Request())
# # #                 time.sleep(1.0)

# # #         # 최종 종료
# # #         self.call(self.cli_h, Trigger.Request())
# # #         self.get_logger().info("🎉 ALL SEQUENCE DONE")

# # # def main():
# # #     rclpy.init()
# # #     node = MasterNode()
# # #     node.run()
# # #     rclpy.shutdown()

# # # if __name__ == '__main__':
# # #     main()

# # import rclpy
# # from rclpy.node import Node
# # from srvs_pkg.srv import GetTargetPose
# # from std_srvs.srv import SetBool, Trigger
# # import time

# # class MasterNode(Node):
# #     def __init__(self):
# #         super().__init__('master_node')
# #         self.cli_v = self.create_client(GetTargetPose, '/get_target_pose')
# #         self.cli_r = self.create_client(GetTargetPose, '/robot_move_step')
# #         self.cli_g = self.create_client(SetBool, '/control_gripper')
# #         self.cli_h = self.create_client(Trigger, '/robot_home')
        
# #         self.Z_OFF = -85.0
# #         self.Z_MARGIN = 20.0
# #         self.BLOCK_H = 16.0
# #         self.WAIT_TIME = 1.5 

# #     def call(self, cli, req):
# #         while not cli.wait_for_service(timeout_sec=1.0):
# #             self.get_logger().info(f'Waiting for {cli.srv_name}...')
# #         future = cli.call_async(req)
# #         rclpy.spin_until_future_complete(self, future)
# #         return future.result()

# #     def count_color(self, color):
# #         p = self.call(self.cli_v, GetTargetPose.Request(target_color=f"count_{color}"))
# #         return int(p.x) if p.success else 0

# #     def find_target_with_retry(self, color, retries=4):
# #         for i in range(retries):
# #             p = self.call(self.cli_v, GetTargetPose.Request(target_color=color))
# #             if p.success:
# #                 return p
# #             self.get_logger().warn(f"⚠️ [{color}] 베이스 찾는 중... ({i+1}/{retries})")
# #             time.sleep(1.0) 
# #         return None

# #     def pick_target(self, color):
# #         self.get_logger().info(f"\n--- PICK TARGET: [{color.upper()}] ---")
# #         p = self.find_target_with_retry(color)
# #         if not p: return False
# #         req = GetTargetPose.Request(); req.yaw = p.yaw; req.target_size = "YAW"
# #         self.call(self.cli_r, req)
# #         time.sleep(self.WAIT_TIME) 

# #         p = self.find_target_with_retry(color)
# #         if not p: return False
# #         req = GetTargetPose.Request(); req.x = p.x; req.y = p.y; req.target_size = "XY"
# #         self.call(self.cli_r, req)
# #         time.sleep(self.WAIT_TIME) 

# #         p = self.find_target_with_retry(color)
# #         if not p: return False
# #         z_move = p.z * 1000.0 + self.Z_OFF
# #         self.call(self.cli_r, GetTargetPose.Request(z=z_move - self.Z_MARGIN, target_size="Z"))
# #         time.sleep(self.WAIT_TIME) 
# #         self.call(self.cli_r, GetTargetPose.Request(z=self.Z_MARGIN, target_size="Z"))
# #         time.sleep(self.WAIT_TIME) 

# #         self.call(self.cli_g, SetBool.Request(data=True))
# #         time.sleep(self.WAIT_TIME) 
# #         self.call(self.cli_r, GetTargetPose.Request(z=-50.0, target_size="Z"))
# #         time.sleep(self.WAIT_TIME) 
# #         return True

# #     def blind_insert(self, base_pose, layer_index, yaw_offset=0.0):
# #         self.get_logger().info(f"\n--- BLIND STACK: Layer {layer_index} (Yaw Offset: +{yaw_offset}도) ---")
# #         time.sleep(1.0)

# #         req_y = GetTargetPose.Request()
# #         req_y.yaw = base_pose.yaw + yaw_offset 
# #         req_y.target_size = "YAW"
# #         self.call(self.cli_r, req_y)
# #         time.sleep(self.WAIT_TIME) 
        
# #         req_xy = GetTargetPose.Request()
# #         req_xy.x = base_pose.x; req_xy.y = base_pose.y; req_xy.target_size = "XY"
# #         self.call(self.cli_r, req_xy)
# #         time.sleep(self.WAIT_TIME) 

# #         z_move = (base_pose.z * 1000.0 + self.Z_OFF) - (self.BLOCK_H * layer_index)
        
# #         self.call(self.cli_r, GetTargetPose.Request(z=z_move - self.Z_MARGIN, target_size="Z"))
# #         time.sleep(self.WAIT_TIME) 
# #         self.call(self.cli_r, GetTargetPose.Request(z=self.Z_MARGIN, target_size="Z"))
# #         time.sleep(self.WAIT_TIME) 

# #         self.call(self.cli_g, SetBool.Request(data=False))
# #         time.sleep(self.WAIT_TIME) 
# #         self.call(self.cli_r, GetTargetPose.Request(z=-50.0, target_size="Z"))
# #         time.sleep(self.WAIT_TIME) 
# #         return True

# #     # =========================================================
# #     # 🧠 최적화 알고리즘 (레시피 수정 반영)
# #     # =========================================================
# #     def get_best_build_plan(self, current_inventory):
# #         # 🌟 당근과 신호등의 초록색(green)을 파란색(blue)으로 수정했습니다.
# #         recipes = {
# #             'battery': {'2x2_yellow': 1, '2x2_blue': 1},
# #             'magnet': {'2x2_blue': 1, '2x2_red': 1},
# #             'e_stop': {'2x2_red': 1, '4x2_yellow': 1},
# #             'carrot': {'2x2_blue': 1, '2x2_yellow': 2},               # 초록 -> 파란색으로 변경
# #             'traffic_light': {'2x2_red': 1, '2x2_yellow': 1, '2x2_blue': 1}, # 초록 -> 파란색으로 변경
# #             'small_tree': {'2x2_red': 1, '4x2_red': 1, '2x2_yellow': 1},
# #             'hammer': {'4x2_blue': 1, '2x2_red': 2}
# #         }
# #         best_plan = []
# #         min_remainder = sum(current_inventory.values())

# #         def dfs(inv, current_plan):
# #             nonlocal best_plan, min_remainder
# #             made_any = False
# #             for name, recipe in recipes.items():
# #                 can_make = True
# #                 for color, count in recipe.items():
# #                     if inv.get(color, 0) < count:
# #                         can_make = False
# #                         break
# #                 if can_make:
# #                     made_any = True
# #                     new_inv = inv.copy()
# #                     for color, count in recipe.items():
# #                         new_inv[color] -= count
# #                     dfs(new_inv, current_plan + [name])
            
# #             if not made_any:
# #                 remainder = sum(inv.values())
# #                 if remainder < min_remainder:
# #                     min_remainder = remainder
# #                     best_plan = current_plan
# #                 elif remainder == min_remainder:
# #                     if len(current_plan) > len(best_plan):
# #                         best_plan = current_plan

# #         dfs(current_inventory, [])
# #         return best_plan

# #     # =========================================================
# #     # 조립 레시피 (당근/신호등 베이스 수정 반영)
# #     # =========================================================
# #     def build_battery(self):
# #         self.get_logger().info("🔋 [배터리] 노란색(Pick) -> 파란색(Base)")
# #         if self.pick_target("2x2_yellow"):
# #             self.call(self.cli_h, Trigger.Request())
# #             base_pose = self.find_target_with_retry("2x2_blue")
# #             if base_pose:
# #                 self.blind_insert(base_pose, layer_index=1)
# #                 self.get_logger().info("✅ 배터리 조립 완료!")

# #     def build_magnet(self):
# #         self.get_logger().info("🧲 [자석] 파란색(Pick) -> 빨간색(Base)")
# #         if self.pick_target("2x2_blue"):
# #             self.call(self.cli_h, Trigger.Request())
# #             base_pose = self.find_target_with_retry("2x2_red")
# #             if base_pose:
# #                 self.blind_insert(base_pose, layer_index=1)
# #                 self.get_logger().info("✅ 자석 조립 완료!")

# #     def build_e_stop(self):
# #         self.get_logger().info("🛑 [비상정지] 빨간색(Pick) -> 노란색4x2(Base)")
# #         if self.pick_target("2x2_red"):
# #             self.call(self.cli_h, Trigger.Request())
# #             base_pose = self.find_target_with_retry("4x2_yellow")
# #             if base_pose:
# #                 self.blind_insert(base_pose, layer_index=1, yaw_offset=-90.0)
# #                 self.get_logger().info("✅ 비상정지 조립 완료!")

# #     def build_carrot(self):
# #         # 🌟 로그 메시지를 파란색(Base)으로 수정했습니다.
# #         self.get_logger().info("🥕 [당근] 노란색(Pick) -> 파란색(Base) -> 노란색(Pick)")
# #         if self.pick_target("2x2_yellow"):
# #             self.call(self.cli_h, Trigger.Request())
            
# #             # 🌟 1층 베이스 탐색 색상을 초록색에서 파란색으로 변경했습니다.
# #             base_pose = self.find_target_with_retry("2x2_blue") # 파란색 1층 베이스 스캔
# #             if base_pose:
# #                 self.blind_insert(base_pose, layer_index=1) # 파란색 위에 노란색 꽂음
# #                 self.call(self.cli_h, Trigger.Request())
                
# #                 if self.pick_target("2x2_yellow"):
# #                     self.call(self.cli_h, Trigger.Request())
# #                     self.blind_insert(base_pose, layer_index=2) # 노란색 위에 노란색 꽂음
# #                     self.get_logger().info("✅ 당근 완성!")

# #     def build_traffic_light(self):
# #         # 🌟 로그 메시지를 파란색(Base)으로 수정했습니다.
# #         self.get_logger().info("🚦 [신호등] 노란색(Pick) -> 파란색(Base) -> 빨간색(Pick)")
# #         if self.pick_target("2x2_yellow"):
# #             self.call(self.cli_h, Trigger.Request())
            
# #             # 🌟 1층 베이스 탐색 색상을 초록색에서 파란색으로 변경했습니다.
# #             base_pose = self.find_target_with_retry("2x2_blue") # 파란색 1층 베이스 스캔
# #             if base_pose:
# #                 self.blind_insert(base_pose, layer_index=1) # 파란색 위에 노란색 꽂음
# #                 self.call(self.cli_h, Trigger.Request())
                
# #                 if self.pick_target("2x2_red"):
# #                     self.call(self.cli_h, Trigger.Request())
# #                     self.blind_insert(base_pose, layer_index=2) # 노란색 위에 빨간색 꽂음
# #                     self.get_logger().info("✅ 신호등 완성!")

# #     def build_small_tree(self):
# #         self.get_logger().info("🌳 [작은 나무] 빨강4x2(Pick) -> 노랑2x2(Base) -> 빨강2x2(Pick)")
# #         if self.pick_target("4x2_red"):
# #             self.call(self.cli_h, Trigger.Request())
# #             base_pose = self.find_target_with_retry("2x2_yellow")
# #             if base_pose:
# #                 self.blind_insert(base_pose, layer_index=1)
# #                 self.call(self.cli_h, Trigger.Request())
                
# #                 if self.pick_target("2x2_red"):
# #                     self.call(self.cli_h, Trigger.Request())
# #                     self.blind_insert(base_pose, layer_index=2)
# #                     self.get_logger().info("✅ 작은 나무 완성!")

# #     def build_hammer(self):
# #         self.get_logger().info("🔨 [망치] 빨강2x2(Pick) -> 빨강2x2(Base) -> 파랑4x2(Pick)")
# #         if self.pick_target("2x2_red"):
# #             self.call(self.cli_h, Trigger.Request())
# #             base_pose = self.find_target_with_retry("2x2_red")
# #             if base_pose:
# #                 self.blind_insert(base_pose, layer_index=1)
# #                 self.call(self.cli_h, Trigger.Request())
                
# #                 if self.pick_target("4x2_blue"):
# #                     self.call(self.cli_h, Trigger.Request())
# #                     self.blind_insert(base_pose, layer_index=2, yaw_offset=90.0)
# #                     self.get_logger().info("✅ 망치 완성!")

# #     # =========================================================
# #     # 메인 루프
# #     # =========================================================
# #     def run(self):
# #         self.get_logger().info("🚀 STARTING BLIND-STACK ASSEMBLY SEQUENCE (AI Optimized)")
# #         self.call(self.cli_h, Trigger.Request())
# #         self.call(self.cli_g, SetBool.Request(data=False))
# #         time.sleep(1.0) 
        
# #         self.get_logger().info("👀 필드 블록 스캔 중...")
# #         inventory = {
# #             "2x2_yellow": self.count_color("2x2_yellow"),
# #             "2x2_blue": self.count_color("2x2_blue"),
# #             "2x2_red": self.count_color("2x2_red"),
# #             "2x2_green": self.count_color("2x2_green"),
# #             "4x2_yellow": self.count_color("4x2_yellow"),
# #             "4x2_red": self.count_color("4x2_red"),
# #             "4x2_blue": self.count_color("4x2_blue")
# #         }
# #         self.get_logger().info(f"📦 현재 인벤토리: {inventory}")

# #         best_plan = self.get_best_build_plan(inventory)
        
# #         if not best_plan:
# #             self.get_logger().warn("❌ 조립 가능한 조합이 없습니다.")
# #         else:
# #             self.get_logger().info(f"🧠 최적 계획: {best_plan}")
# #             for item in best_plan:
# #                 self.get_logger().info(f"▶️ 작업 시작: {item.upper()}")
# #                 if item == 'battery': self.build_battery()
# #                 elif item == 'magnet': self.build_magnet()
# #                 elif item == 'e_stop': self.build_e_stop()
# #                 elif item == 'carrot': self.build_carrot()
# #                 elif item == 'traffic_light': self.build_traffic_light()
# #                 elif item == 'small_tree': self.build_small_tree()
# #                 elif item == 'hammer': self.build_hammer()
                    
# #                 self.call(self.cli_h, Trigger.Request())
# #                 time.sleep(1.0)

# #         self.call(self.cli_h, Trigger.Request())
# #         self.get_logger().info("🎉 ALL SEQUENCE DONE")

# # def main():
# #     rclpy.init()
# #     node = MasterNode()
# #     node.run()
# #     rclpy.shutdown()

# # if __name__ == '__main__':
# #     main()

# import rclpy
# from rclpy.node import Node
# from srvs_pkg.srv import GetTargetPose
# from std_srvs.srv import SetBool, Trigger
# import time

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
#             self.get_logger().warn(f"⚠️ [{color}] 베이스 찾는 중... ({i+1}/{retries})")
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

#     def blind_insert(self, base_pose, layer_index, yaw_offset=0.0):
#         self.get_logger().info(f"\n--- BLIND STACK: Layer {layer_index} (Yaw Offset: +{yaw_offset}도) ---")
#         time.sleep(1.0)

#         req_y = GetTargetPose.Request()
#         req_y.yaw = base_pose.yaw + yaw_offset 
#         req_y.target_size = "YAW"
#         self.call(self.cli_r, req_y)
#         time.sleep(self.WAIT_TIME) 
        
#         req_xy = GetTargetPose.Request()
#         req_xy.x = base_pose.x; req_xy.y = base_pose.y; req_xy.target_size = "XY"
#         self.call(self.cli_r, req_xy)
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

#     # =========================================================
#     # 🧠 최적화 알고리즘
#     # =========================================================
#     def get_best_build_plan(self, current_inventory):
#         recipes = {
#             'battery': {'2x2_yellow': 1, '2x2_blue': 1},
#             'magnet': {'2x2_blue': 1, '2x2_red': 1},
#             'e_stop': {'2x2_red': 1, '4x2_yellow': 1},
#             'carrot': {'2x2_blue': 1, '2x2_yellow': 2},
#             'traffic_light': {'2x2_red': 1, '2x2_yellow': 1, '2x2_blue': 1},
#             'small_tree': {'2x2_red': 1, '4x2_red': 1, '2x2_yellow': 1},
#             'hammer': {'4x2_blue': 1, '2x2_red': 2}
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

#     # =========================================================
#     # 조립 레시피 (잔진동 대기시간 time.sleep(1.0) 추가 적용)
#     # =========================================================
#     def build_battery(self):
#         self.get_logger().info("🔋 [배터리] 노란색(Pick) -> 파란색(Base)")
#         if self.pick_target("2x2_yellow"):
#             self.call(self.cli_h, Trigger.Request())
            
#             # 🌟 로봇 팔 정지 후 잔진동이 사라질 때까지 1.0초 대기
#             time.sleep(1.0) 
            
#             base_pose = self.find_target_with_retry("2x2_blue")
#             if base_pose:
#                 self.blind_insert(base_pose, layer_index=1)
#                 self.get_logger().info("✅ 배터리 조립 완료!")

#     def build_magnet(self):
#         self.get_logger().info("🧲 [자석] 파란색(Pick) -> 빨간색(Base)")
#         if self.pick_target("2x2_blue"):
#             self.call(self.cli_h, Trigger.Request())
            
#             # 🌟 잔진동 대기
#             time.sleep(1.0) 
            
#             base_pose = self.find_target_with_retry("2x2_red")
#             if base_pose:
#                 self.blind_insert(base_pose, layer_index=1)
#                 self.get_logger().info("✅ 자석 조립 완료!")

#     def build_e_stop(self):
#         self.get_logger().info("🛑 [비상정지] 빨간색(Pick) -> 노란색4x2(Base)")
#         if self.pick_target("2x2_red"):
#             self.call(self.cli_h, Trigger.Request())
            
#             # 🌟 잔진동 대기
#             time.sleep(1.0) 
            
#             base_pose = self.find_target_with_retry("4x2_yellow")
#             if base_pose:
#                 self.blind_insert(base_pose, layer_index=1, yaw_offset=-90.0)
#                 self.get_logger().info("✅ 비상정지 조립 완료!")

#     def build_carrot(self):
#         self.get_logger().info("🥕 [당근] 노란색(Pick) -> 파란색(Base) -> 노란색(Pick)")
#         if self.pick_target("2x2_yellow"):
#             self.call(self.cli_h, Trigger.Request())
            
#             # 🌟 잔진동 대기
#             time.sleep(1.0) 
            
#             base_pose = self.find_target_with_retry("2x2_blue") 
#             if base_pose:
#                 self.blind_insert(base_pose, layer_index=1) 
#                 self.call(self.cli_h, Trigger.Request())
                
#                 if self.pick_target("2x2_yellow"):
#                     self.call(self.cli_h, Trigger.Request())
#                     # 여기서는 카메라로 베이스를 스캔하지 않으므로, 추가 대기 없이 바로 블라인드 스택!
#                     self.blind_insert(base_pose, layer_index=2) 
#                     self.get_logger().info("✅ 당근 완성!")

#     def build_traffic_light(self):
#         self.get_logger().info("🚦 [신호등] 노란색(Pick) -> 파란색(Base) -> 빨간색(Pick)")
#         if self.pick_target("2x2_yellow"):
#             self.call(self.cli_h, Trigger.Request())
            
#             # 🌟 잔진동 대기
#             time.sleep(1.0) 
            
#             base_pose = self.find_target_with_retry("2x2_blue") 
#             if base_pose:
#                 self.blind_insert(base_pose, layer_index=1) 
#                 self.call(self.cli_h, Trigger.Request())
                
#                 if self.pick_target("2x2_red"):
#                     self.call(self.cli_h, Trigger.Request())
#                     self.blind_insert(base_pose, layer_index=2) 
#                     self.get_logger().info("✅ 신호등 완성!")

#     def build_small_tree(self):
#         self.get_logger().info("🌳 [작은 나무] 빨강4x2(Pick) -> 노랑2x2(Base) -> 빨강2x2(Pick)")
#         if self.pick_target("4x2_red"):
#             self.call(self.cli_h, Trigger.Request())
            
#             # 🌟 잔진동 대기
#             time.sleep(1.0) 
            
#             base_pose = self.find_target_with_retry("2x2_yellow")
#             if base_pose:
#                 self.blind_insert(base_pose, layer_index=1)
#                 self.call(self.cli_h, Trigger.Request())
                
#                 if self.pick_target("2x2_red"):
#                     self.call(self.cli_h, Trigger.Request())
#                     self.blind_insert(base_pose, layer_index=2)
#                     self.get_logger().info("✅ 작은 나무 완성!")

#     def build_hammer(self):
#         self.get_logger().info("🔨 [망치] 빨강2x2(Pick) -> 빨강2x2(Base) -> 파랑4x2(Pick)")
#         if self.pick_target("2x2_red"):
#             self.call(self.cli_h, Trigger.Request())
            
#             # 🌟 잔진동 대기
#             time.sleep(1.0) 
            
#             base_pose = self.find_target_with_retry("2x2_red")
#             if base_pose:
#                 self.blind_insert(base_pose, layer_index=1)
#                 self.call(self.cli_h, Trigger.Request())
                
#                 if self.pick_target("4x2_blue"):
#                     self.call(self.cli_h, Trigger.Request())
#                     self.blind_insert(base_pose, layer_index=2, yaw_offset=90.0)
#                     self.get_logger().info("✅ 망치 완성!")

#     # =========================================================
#     # 메인 루프
#     # =========================================================
#     def run(self):
#         self.get_logger().info("🚀 STARTING BLIND-STACK ASSEMBLY SEQUENCE (AI Optimized)")
#         self.call(self.cli_h, Trigger.Request())
#         self.call(self.cli_g, SetBool.Request(data=False))
#         time.sleep(1.0) 
        
#         self.get_logger().info("👀 필드 블록 스캔 중...")
#         inventory = {
#             "2x2_yellow": self.count_color("2x2_yellow"),
#             "2x2_blue": self.count_color("2x2_blue"),
#             "2x2_red": self.count_color("2x2_red"),
#             "2x2_green": self.count_color("2x2_green"),
#             "4x2_yellow": self.count_color("4x2_yellow"),
#             "4x2_red": self.count_color("4x2_red"),
#             "4x2_blue": self.count_color("4x2_blue")
#         }
#         self.get_logger().info(f"📦 현재 인벤토리: {inventory}")

#         best_plan = self.get_best_build_plan(inventory)
        
#         if not best_plan:
#             self.get_logger().warn("❌ 조립 가능한 조합이 없습니다.")
#         else:
#             self.get_logger().info(f"🧠 최적 계획: {best_plan}")
#             for item in best_plan:
#                 self.get_logger().info(f"▶️ 작업 시작: {item.upper()}")
#                 if item == 'battery': self.build_battery()
#                 elif item == 'magnet': self.build_magnet()
#                 elif item == 'e_stop': self.build_e_stop()
#                 elif item == 'carrot': self.build_carrot()
#                 elif item == 'traffic_light': self.build_traffic_light()
#                 elif item == 'small_tree': self.build_small_tree()
#                 elif item == 'hammer': self.build_hammer()
                    
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
            self.get_logger().warn(f"⚠️ [{color}] 베이스 찾는 중... ({i+1}/{retries})")
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

    # 🌟 핵심 수정: XY 이동을 먼저 수행하고, 그 다음 YAW를 회전합니다.
    def blind_insert(self, base_pose, layer_index, yaw_offset=0.0):
        self.get_logger().info(f"\n--- BLIND STACK: Layer {layer_index} (Yaw Offset: +{yaw_offset}도) ---")
        time.sleep(1.0)

        # 1. XY를 먼저 이동 (베이스 좌표와 오프셋 그대로 적용)
        req_xy = GetTargetPose.Request()
        req_xy.x = base_pose.x; req_xy.y = base_pose.y; req_xy.target_size = "XY"
        self.call(self.cli_r, req_xy)
        time.sleep(self.WAIT_TIME) 

        # 2. 타겟 위에 도착한 상태에서 YAW 이동 (제자리 회전)
        req_y = GetTargetPose.Request()
        req_y.yaw = base_pose.yaw + yaw_offset 
        req_y.target_size = "YAW"
        self.call(self.cli_r, req_y)
        time.sleep(self.WAIT_TIME) 

        # 3. Z축 내려가기
        z_move = (base_pose.z * 1000.0 + self.Z_OFF) - (self.BLOCK_H * layer_index)
        
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

    # =========================================================
    # 🧠 최적화 알고리즘
    # =========================================================
    def get_best_build_plan(self, current_inventory):
        recipes = {
            'battery': {'2x2_yellow': 1, '2x2_blue': 1},
            'magnet': {'2x2_blue': 1, '2x2_red': 1},
            'e_stop': {'2x2_red': 1, '4x2_yellow': 1},
            'carrot': {'2x2_blue': 1, '2x2_yellow': 2},
            'traffic_light': {'2x2_red': 1, '2x2_yellow': 1, '2x2_blue': 1},
            'small_tree': {'2x2_red': 1, '4x2_red': 1, '2x2_yellow': 1},
            'hammer': {'4x2_blue': 1, '2x2_red': 2}
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

    # =========================================================
    # 조립 레시피 (잔진동 대기시간 time.sleep(1.0) 유지)
    # =========================================================
    def build_battery(self):
        self.get_logger().info("🔋 [배터리] 노란색(Pick) -> 파란색(Base)")
        if self.pick_target("2x2_yellow"):
            self.call(self.cli_h, Trigger.Request())
            time.sleep(1.0) 
            base_pose = self.find_target_with_retry("2x2_blue")
            if base_pose:
                self.blind_insert(base_pose, layer_index=1)
                self.get_logger().info("✅ 배터리 조립 완료!")

    def build_magnet(self):
        self.get_logger().info("🧲 [자석] 파란색(Pick) -> 빨간색(Base)")
        if self.pick_target("2x2_blue"):
            self.call(self.cli_h, Trigger.Request())
            time.sleep(1.0) 
            base_pose = self.find_target_with_retry("2x2_red")
            if base_pose:
                self.blind_insert(base_pose, layer_index=1)
                self.get_logger().info("✅ 자석 조립 완료!")

    def build_e_stop(self):
        self.get_logger().info("🛑 [비상정지] 빨간색(Pick) -> 노란색4x2(Base)")
        if self.pick_target("2x2_red"):
            self.call(self.cli_h, Trigger.Request())
            time.sleep(1.0) 
            base_pose = self.find_target_with_retry("4x2_yellow")
            if base_pose:
                self.blind_insert(base_pose, layer_index=1, yaw_offset=-90.0)
                self.get_logger().info("✅ 비상정지 조립 완료!")

    def build_carrot(self):
        self.get_logger().info("🥕 [당근] 노란색(Pick) -> 파란색(Base) -> 노란색(Pick)")
        if self.pick_target("2x2_yellow"):
            self.call(self.cli_h, Trigger.Request())
            time.sleep(1.0) 
            base_pose = self.find_target_with_retry("2x2_blue") 
            if base_pose:
                self.blind_insert(base_pose, layer_index=1) 
                self.call(self.cli_h, Trigger.Request())
                
                if self.pick_target("2x2_yellow"):
                    self.call(self.cli_h, Trigger.Request())
                    self.blind_insert(base_pose, layer_index=2) 
                    self.get_logger().info("✅ 당근 완성!")

    def build_traffic_light(self):
        self.get_logger().info("🚦 [신호등] 노란색(Pick) -> 파란색(Base) -> 빨간색(Pick)")
        if self.pick_target("2x2_yellow"):
            self.call(self.cli_h, Trigger.Request())
            time.sleep(1.0) 
            base_pose = self.find_target_with_retry("2x2_blue") 
            if base_pose:
                self.blind_insert(base_pose, layer_index=1) 
                self.call(self.cli_h, Trigger.Request())
                
                if self.pick_target("2x2_red"):
                    self.call(self.cli_h, Trigger.Request())
                    self.blind_insert(base_pose, layer_index=2) 
                    self.get_logger().info("✅ 신호등 완성!")

    def build_small_tree(self):
        self.get_logger().info("🌳 [작은 나무] 빨강4x2(Pick) -> 노랑2x2(Base) -> 빨강2x2(Pick)")
        if self.pick_target("4x2_red"):
            self.call(self.cli_h, Trigger.Request())
            time.sleep(1.0) 
            base_pose = self.find_target_with_retry("2x2_yellow")
            if base_pose:
                self.blind_insert(base_pose, layer_index=1)
                self.call(self.cli_h, Trigger.Request())
                
                if self.pick_target("2x2_red"):
                    self.call(self.cli_h, Trigger.Request())
                    self.blind_insert(base_pose, layer_index=2)
                    self.get_logger().info("✅ 작은 나무 완성!")

    def build_hammer(self):
        self.get_logger().info("🔨 [망치] 빨강2x2(Pick) -> 빨강2x2(Base) -> 파랑4x2(Pick)")
        if self.pick_target("2x2_red"):
            self.call(self.cli_h, Trigger.Request())
            time.sleep(1.0) 
            base_pose = self.find_target_with_retry("2x2_red")
            if base_pose:
                self.blind_insert(base_pose, layer_index=1)
                self.call(self.cli_h, Trigger.Request())
                
                if self.pick_target("4x2_blue"):
                    self.call(self.cli_h, Trigger.Request())
                    self.blind_insert(base_pose, layer_index=2, yaw_offset=90.0)
                    self.get_logger().info("✅ 망치 완성!")

    # =========================================================
    # 메인 루프
    # =========================================================
    def run(self):
        self.get_logger().info("🚀 STARTING BLIND-STACK ASSEMBLY SEQUENCE (AI Optimized)")
        self.call(self.cli_h, Trigger.Request())
        self.call(self.cli_g, SetBool.Request(data=False))
        time.sleep(1.0) 
        
        self.get_logger().info("👀 필드 블록 스캔 중...")
        inventory = {
            "2x2_yellow": self.count_color("2x2_yellow"),
            "2x2_blue": self.count_color("2x2_blue"),
            "2x2_red": self.count_color("2x2_red"),
            "2x2_green": self.count_color("2x2_green"),
            "4x2_yellow": self.count_color("4x2_yellow"),
            "4x2_red": self.count_color("4x2_red"),
            "4x2_blue": self.count_color("4x2_blue")
        }
        self.get_logger().info(f"📦 현재 인벤토리: {inventory}")

        best_plan = self.get_best_build_plan(inventory)
        
        if not best_plan:
            self.get_logger().warn("❌ 조립 가능한 조합이 없습니다.")
        else:
            self.get_logger().info(f"🧠 최적 계획: {best_plan}")
            for item in best_plan:
                self.get_logger().info(f"▶️ 작업 시작: {item.upper()}")
                if item == 'battery': self.build_battery()
                elif item == 'magnet': self.build_magnet()
                elif item == 'e_stop': self.build_e_stop()
                elif item == 'carrot': self.build_carrot()
                elif item == 'traffic_light': self.build_traffic_light()
                elif item == 'small_tree': self.build_small_tree()
                elif item == 'hammer': self.build_hammer()
                    
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