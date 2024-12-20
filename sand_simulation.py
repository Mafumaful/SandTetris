import pygame
import random
import sys
import numpy as np

# 初始化 Pygame
pygame.init()

# 常量定义
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 1000
SAND_SIZE = 8  # Increased from 3 to 8 pixels
FPS = 60       # 调整帧率
DIRECTIONS = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
GRID_WIDTH = WINDOW_WIDTH // SAND_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // SAND_SIZE

# 颜色定义
BLACK = (0, 0, 0)
SAND_COLORS = [
    (255, 255, 0),  # Yellow
    (0, 0, 255),    # Blue
    (255, 0, 0),    # Red
]

# 创建窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Sand Simulation')
clock = pygame.time.Clock()

class SandGrain:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = random.choice(SAND_COLORS)
        self.settled = False
        self.sliding = False  # 是否正在滑动

class SandSimulation:
    def __init__(self):
        self.sand_particles = []
        self.grid = np.zeros((WINDOW_WIDTH // SAND_SIZE, WINDOW_HEIGHT // SAND_SIZE), dtype=bool)
        self.max_slope = 1
        self.slide_chance = 0.95
        self.height_threshold = 2
        self.square_size = 20
        self.current_x = WINDOW_WIDTH // 2
        self.move_speed = 2 * SAND_SIZE
        self.active_square = None
        self.can_move = True
        self.flash_timer = None
        self.sand_to_remove = None
        self.flash_duration = 1  # Changed from 100 to 50 milliseconds
        
    def is_square_landed(self):
        """Check if the current square has landed"""
        if not self.active_square:
            return True
            
        for sand in self.active_square:
            if not sand.settled:
                return False
                
        # When square has landed, check and remove connected sand
        if self.flash_timer is None:  # Only start flash if not already flashing
            self.check_and_remove_connected_sand()
        return True

    def move_left(self):
        if not self.can_move or not self.active_square:
            return
            
        # Check if any particle would go out of bounds
        leftmost = min(int(sand.x - self.move_speed) for sand in self.active_square 
                      if not sand.settled)
        if leftmost < 0:
            # Move only as far as the border
            offset = -min(int(sand.x) for sand in self.active_square 
                         if not sand.settled)
            if offset < 0:
                for sand in self.active_square:
                    if not sand.settled:
                        sand.x += offset
            return
            
        # Move all particles in active square
        for sand in self.active_square:
            if not sand.settled:
                new_x = sand.x - self.move_speed
                grid_x = int(new_x // SAND_SIZE)
                grid_y = int(sand.y // SAND_SIZE)
                if not self.grid[grid_x][grid_y]:
                    sand.x = new_x

    def move_right(self):
        if not self.can_move or not self.active_square:
            return
            
        # Check if any particle would go out of bounds
        rightmost = max(int(sand.x + self.move_speed) for sand in self.active_square 
                       if not sand.settled)
        if rightmost >= WINDOW_WIDTH:
            # Move only as far as the border
            offset = WINDOW_WIDTH - max(int(sand.x + SAND_SIZE) for sand in self.active_square 
                                      if not sand.settled)
            if offset > 0:
                for sand in self.active_square:
                    if not sand.settled:
                        sand.x += offset
            return
            
        # Move all particles in active square
        for sand in self.active_square:
            if not sand.settled:
                new_x = sand.x + self.move_speed
                grid_x = int(new_x // SAND_SIZE)
                grid_y = int(sand.y // SAND_SIZE)
                if not self.grid[grid_x][grid_y]:
                    sand.x = new_x
    
    def find_connected_sand(self, start_x, start_y, color, visited):
        """Optimized connected sand finding using numpy operations"""
        if (start_x < 0 or start_x >= WINDOW_WIDTH//SAND_SIZE or
            start_y < 0 or start_y >= WINDOW_HEIGHT//SAND_SIZE or
            not self.grid[start_x, start_y] or
            (start_x, start_y) in visited):
            return set()
        
        # Find the sand particle at this position using dictionary lookup
        grid_pos = (start_x, start_y)
        sand_at_pos = self.particle_lookup.get(grid_pos)
        
        if not sand_at_pos or sand_at_pos.color != color:
            return set()
        
        connected = set()
        stack = [(start_x, start_y)]
        
        while stack:
            x, y = stack.pop()
            if (x, y) in visited:
                continue
            
            current_sand = self.particle_lookup.get((x, y))
            if not current_sand or current_sand.color != color:
                continue
            
            visited.add((x, y))
            connected.add((x, y))
            
            # Check neighbors more efficiently
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                next_x, next_y = x + dx, y + dy
                if (0 <= next_x < WINDOW_WIDTH//SAND_SIZE and
                    0 <= next_y < WINDOW_HEIGHT//SAND_SIZE and
                    self.grid[next_x, next_y] and
                    (next_x, next_y) not in visited):
                    stack.append((next_x, next_y))
        
        return connected
    
    def check_and_remove_connected_sand(self):
        """Check for same-colored sand that touches both bounds and remove it after flashing"""
        current_time = pygame.time.get_ticks()
        
        # Handle removal after flash
        if self.flash_timer is not None:
            if current_time - self.flash_timer >= self.flash_duration:
                if self.sand_to_remove:
                    # Update grid
                    for x, y in self.sand_to_remove:
                        self.grid[x][y] = False
                    
                    # Remove particles
                    self.sand_particles = [sand for sand in self.sand_particles 
                                         if (int(sand.x//SAND_SIZE), 
                                             int(sand.y//SAND_SIZE)) not in self.sand_to_remove]
                    
                    # Clear active square if all its particles were removed
                    if self.active_square:
                        self.active_square = [sand for sand in self.active_square 
                                            if sand in self.sand_particles]
                
                self.flash_timer = None
                self.sand_to_remove = None
            return
            
        visited = set()
        all_connected = set()
        
        # Check for connections from left wall
        for y in range(WINDOW_HEIGHT // SAND_SIZE):
            if not self.grid[0][y]:
                continue
                
            # Find sand at left wall
            left_sand = None
            for sand in self.sand_particles:
                if (int(sand.x//SAND_SIZE), int(sand.y//SAND_SIZE)) == (0, y):
                    left_sand = sand
                    break
            
            if left_sand:
                # Find all connected sand of the same color
                connected = self.find_connected_sand(0, y, left_sand.color, visited)
                
                # Check if this group reaches the right wall
                if any(x == (WINDOW_WIDTH//SAND_SIZE - 1) for x, _ in connected):
                    all_connected.update(connected)
        
        # Start flash timer if connected sand is found
        if all_connected and not self.flash_timer:
            self.flash_timer = current_time
            self.sand_to_remove = all_connected
            
    def add_sand_square(self, center_x):
        # Calculate the top-left corner of the square
        start_x = center_x - (self.square_size * SAND_SIZE) // 2
        
        # Choose one random color for the entire square
        square_color = random.choice(SAND_COLORS)
        
        # Store the new square's particles
        new_square = []
        
        # Add sand particles in a square pattern
        for row in range(self.square_size):
            for col in range(self.square_size):
                x = start_x + (col * SAND_SIZE)
                y = row * SAND_SIZE
                
                # Ensure the sand is within screen bounds
                if 0 <= x < WINDOW_WIDTH and 0 <= y < WINDOW_HEIGHT:
                    grid_x = int(x // SAND_SIZE)
                    grid_y = int(y // SAND_SIZE)
                    
                    if not self.grid[grid_x][grid_y]:
                        new_sand = SandGrain(x, y)
                        new_sand.color = square_color
                        new_square.append(new_sand)
                        self.sand_particles.append(new_sand)
        
        self.active_square = new_square
        self.can_move = True  # Reset movement control for new square
    
    def check_slope(self, x, y):
        # 检查左右两侧的高度差
        left_height = 0
        right_height = 0
        
        # 检查左侧高度差
        if x > 0:
            check_y = y
            while (check_y < (WINDOW_HEIGHT//SAND_SIZE) and 
                   not self.grid[x-1][check_y]):
                left_height += 1
                check_y += 1
                if left_height > self.height_threshold:
                    break
        
        # 检查右侧高度差
        if x < (WINDOW_WIDTH//SAND_SIZE)-1:
            check_y = y
            while (check_y < (WINDOW_HEIGHT//SAND_SIZE) and 
                   not self.grid[x+1][check_y]):
                right_height += 1
                check_y += 1
                if right_height > self.height_threshold:
                    break
        
        # 如果高度差超过阈值，决定滑落方向
        if left_height > self.height_threshold or right_height > self.height_threshold:
            # 优先向高度差更大的方向滑落
            if left_height > right_height:
                return -1 if x > 0 and not self.grid[x-1][y] else 0
            elif right_height > left_height:
                return 1 if x < (WINDOW_WIDTH//SAND_SIZE)-1 and not self.grid[x+1][y] else 0
            else:
                # 如果两边高度差相同，随机选择方向
                possible_dirs = []
                if x > 0 and not self.grid[x-1][y]:
                    possible_dirs.append(-1)
                if x < (WINDOW_WIDTH//SAND_SIZE)-1 and not self.grid[x+1][y]:
                    possible_dirs.append(1)
                return random.choice(possible_dirs) if possible_dirs else 0
        
        # 如果没��显著的高度差，检查普通的滑动条件
        left_empty = x > 0 and not self.grid[x-1][y]
        right_empty = x < (WINDOW_WIDTH//SAND_SIZE)-1 and not self.grid[x+1][y]
        
        if y < (WINDOW_HEIGHT//SAND_SIZE)-1:
            left_support = x > 0 and self.grid[x-1][y+1]
            center_support = self.grid[x][y+1]
            right_support = x < (WINDOW_WIDTH//SAND_SIZE)-1 and self.grid[x+1][y+1]
            
            if not center_support:
                if left_support and right_support:
                    return random.choice([-1, 1]) if random.random() < 0.5 else 0
                elif left_support and left_empty:
                    return 1
                elif right_support and right_empty:
                    return -1
                elif left_empty and right_empty:
                    return random.choice([-1, 1])
        return 0
    
    def update(self):
        any_movement = False
        any_settled_this_frame = False
        
        # Update particle lookup for this frame
        self.update_particle_lookup()
        
        # Check active square state
        if self.active_square and self.can_move:
            for sand in self.active_square:
                if not sand.settled:
                    new_y = int((sand.y + SAND_SIZE) // SAND_SIZE)
                    new_x = int(sand.x // SAND_SIZE)
                    if (new_y >= WINDOW_HEIGHT//SAND_SIZE or 
                        (new_y < WINDOW_HEIGHT//SAND_SIZE and self.grid[new_x, new_y])):
                        self.can_move = False
                        break
        
        # Use numpy operations for faster grid updates
        updates = []
        removes = []
        
        for sand in self.sand_particles:
            initial_pos = (sand.x, sand.y)
            was_settled = sand.settled
            
            if sand.settled:
                x, y = int(sand.x // SAND_SIZE), int(sand.y // SAND_SIZE)
                slide_direction = self.check_slope(x, y)
                if slide_direction != 0 and random.random() < self.slide_chance:
                    removes.append((x, y))
                    sand.settled = False
                    new_x = (x + slide_direction) * SAND_SIZE
                    if 0 <= new_x < WINDOW_WIDTH and not self.grid[x + slide_direction, y]:
                        sand.x = new_x
                        any_movement = True
                continue
            
            new_x = int(sand.x // SAND_SIZE)
            new_y = int((sand.y + SAND_SIZE) // SAND_SIZE)
            
            if new_y >= WINDOW_HEIGHT//SAND_SIZE or self.grid[new_x, new_y]:
                current_y = int(sand.y // SAND_SIZE)
                slide_direction = self.check_slope(new_x, current_y)
                if slide_direction != 0:
                    test_x = new_x + slide_direction
                    if (0 <= test_x < WINDOW_WIDTH//SAND_SIZE and 
                        not self.grid[test_x, current_y]):
                        sand.x = test_x * SAND_SIZE
                        any_movement = True
                        continue
                
                sand.settled = True
                updates.append((new_x, current_y))
                sand.x = new_x * SAND_SIZE
                sand.y = current_y * SAND_SIZE
                
                if not was_settled:
                    any_settled_this_frame = True
                continue
            
            if not self.grid[new_x, new_y]:
                sand.y += SAND_SIZE
                any_movement = True
            
            if (sand.x, sand.y) != initial_pos:
                any_movement = True
        
        # Batch update the grid
        for x, y in removes:
            self.grid[x, y] = False
        for x, y in updates:
            self.grid[x, y] = True
        
        if any_settled_this_frame or not any_movement:
            self.check_and_remove_connected_sand()
    
    def draw(self, surface):
        WHITE = (255, 255, 255)
        
        for sand in self.sand_particles:
            color = sand.color
            # If sand is marked for removal and flashing, draw it white
            if (self.sand_to_remove and 
                (int(sand.x//SAND_SIZE), int(sand.y//SAND_SIZE)) in self.sand_to_remove):
                color = WHITE
                
            pygame.draw.rect(surface, color, 
                           (int(sand.x), int(sand.y), SAND_SIZE, SAND_SIZE))
    
    def update_particle_lookup(self):
        """Maintain a dictionary of particle positions for quick lookup"""
        self.particle_lookup = {
            (int(sand.x//SAND_SIZE), int(sand.y//SAND_SIZE)): sand 
            for sand in self.sand_particles
        }

def main():
    simulation = SandSimulation()
    running = True
    
    # Spawn the first square
    simulation.add_sand_square(WINDOW_WIDTH // 2)
    simulation.current_x = WINDOW_WIDTH // 2

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Handle keyboard input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            simulation.move_left()
        if keys[pygame.K_RIGHT]:
            simulation.move_right()
        
        # Update sand positions
        simulation.update()
        
        # Only spawn new square if previous one has landed and flash/removal is complete
        if (simulation.is_square_landed() and 
            simulation.flash_timer is None and 
            simulation.sand_to_remove is None):
            simulation.current_x = WINDOW_WIDTH // 2
            simulation.add_sand_square(simulation.current_x)
        
        # Draw
        screen.fill(BLACK)
        simulation.draw(screen)
        pygame.display.flip()
        
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()