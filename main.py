import random
import heapq
from collections import deque
import time
import pygame
import csv  
import os  
import collections

# --- Konstanta Arah (opsional, untuk kejelasan) ---
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# --- Konstanta Pygame ---
BLOCK_SIZE = 20  # Ukuran setiap kotak grid dalam piksel
(W_PAD, H_PAD) = (0, 0) 

COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREEN = (0, 200, 0)
COLOR_GREEN_DARK = (0, 150, 0)
COLOR_RED = (200, 0, 0)
COLOR_GRAY = (100, 100, 100)

class SnakeGame:
    def __init__(self, width, height, static_obstacles=None, food_trigger=0, obstacle_spawn_count=(0,0)):
        self.width = width
        self.height = height
        self.grid_size = (width, height)
        
        self.static_obstacles = set(static_obstacles) if static_obstacles else set()
        self.dynamic_obstacles = set()
        
        # Konfigurasi obstacle dinamis
        self.food_trigger_threshold = food_trigger
        self.obstacle_spawn_min = obstacle_spawn_count[0] 
        self.obstacle_spawn_max = obstacle_spawn_count[1] 
        self.food_eaten_counter = 0
        
        # Inisialisasi ular
        start_pos = (1, 1) # (Posisi spawn aman)
        self.snake = deque([start_pos])
        self.snake_body_set = {start_pos} 
        
        self.food = None
        self.place_food()
        
        self.game_over = False
        self.score = 0
        self.steps = 0
        self.max_steps = 1000
        self.game_over_reason = "" # Inisialisasi

    def place_food(self):
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            pos = (x, y)
            # Pastikan makanan tidak muncul di atas ular atau rintangan
            if (pos not in self.snake_body_set and
                pos not in self.static_obstacles and
                pos not in self.dynamic_obstacles): 
                
                self.food = pos
                return

    def place_dynamic_obstacle(self):
        max_attempts = 50 
        for _ in range(max_attempts):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            pos = (x, y)
            
            # Pastikan tidak spawn di atas ular, makanan, atau obstacle lain
            if pos not in self.snake_body_set and \
               pos not in self.static_obstacles and \
               pos not in self.dynamic_obstacles and \
               pos != self.food:
                
                self.dynamic_obstacles.add(pos)
                return True # <-- BERHASIL
        
        return False # <-- GAGAL (setelah 50x percobaan)

    def get_valid_neighbors(self, pos):
        neighbors = []
        x, y = pos
        for dx, dy in [UP, DOWN, LEFT, RIGHT]:
            nx, ny = x + dx, y + dy
            new_pos = (nx, ny)
            if 0 <= nx < self.width and 0 <= ny < self.height and \
               new_pos not in self.static_obstacles and \
               new_pos not in self.dynamic_obstacles: 
                
                if new_pos not in self.snake_body_set:
                     neighbors.append(new_pos)
                elif len(self.snake) > 2 and new_pos == self.snake[-1] and new_pos != self.food:
                 neighbors.append(new_pos)
        return neighbors

    def move(self, direction):
        if self.game_over:
            return

        current_head = self.snake[0]
        dx, dy = direction
        new_head = (current_head[0] + dx, current_head[1] + dy)
        
        self.steps += 1

        # 1. Cek Game Over (Dinding, Rintangan, Self-collision)
        if ( 
           (new_head in self.snake_body_set) or
           (new_head in self.static_obstacles) or
           (new_head in self.dynamic_obstacles) or 
           (not (0 <= new_head[0] < self.width and 0 <= new_head[1] < self.height)) or
           (self.steps >= self.max_steps)
        ):
            
            if new_head in self.snake_body_set: self.game_over_reason = "Self-collision"
            elif new_head in self.static_obstacles: self.game_over_reason = "Hit Static Obstacle"
            elif new_head in self.dynamic_obstacles: self.game_over_reason = "Hit Dynamic Obstacle" 
            elif not (0 <= new_head[0] < self.width and 0 <= new_head[1] < self.height): self.game_over_reason = "Hit Wall"
            elif self.steps >= self.max_steps: self.game_over_reason = "Step Limit Reached"
            
            self.game_over = True
            return

        # 2. Tambahkan kepala baru
        self.snake.appendleft(new_head)
        self.snake_body_set.add(new_head)

        # 3. Cek Makanan
        if new_head == self.food:
            self.score += 1
            # Penting: Panggil place_food() DULU sebelum obstacle,
            # agar obstacle tidak spawn di tempat food baru
            self.place_food() 
            
            # --- Logika Obstacle Dinamis ---
            if self.food_trigger_threshold > 0:
                self.food_eaten_counter += 1
                
                # Jika sudah mencapai threshold 'n'
                if self.food_eaten_counter >= self.food_trigger_threshold:
                    
                    # TENTUKAN JUMLAH OBSTACLE
                    num_to_spawn = random.randint(self.obstacle_spawn_min, self.obstacle_spawn_max)
                    
                    # Panggil fungsi spawn sebanyak num_to_spawn
                    for _ in range(num_to_spawn):
                        # Panggil place_dynamic_obstacle()
                        # Kita tambahkan cek (dari langkah 5) untuk keamanan
                        if not self.place_dynamic_obstacle():
                            # Gagal menempatkan (papan penuh), hentikan spawn
                            break 
                            
                    self.food_eaten_counter = 0 # Reset counter
            
        else:
            # Hapus ekor (ular bergerak)
            tail = self.snake.pop()
            self.snake_body_set.remove(tail)

# --- ALGORITMA PATHFINDING ---

def heuristic_manhattan(a, b):
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)

def find_path_bfs(game, goal):
    start = game.snake[0]
    
    queue = deque([(start, [start])]) # (posisi, path_sejauh_ini)
    visited = {start}
    nodes_expanded = 0

    while queue:
        nodes_expanded += 1
        current_pos, path = queue.popleft()

        if current_pos == goal:
            return path, nodes_expanded # Sukses

        # Eksplorasi tetangga
        for neighbor in game.get_valid_neighbors(current_pos):
            if neighbor not in visited:
                visited.add(neighbor)
                new_path = path + [neighbor]
                queue.append((neighbor, new_path))
    
    return None, nodes_expanded # Gagal (tidak ada jalur)

def find_path_a_star(game, goal):
    start = game.snake[0]
    
    open_set = [(0, start)] # Priority queue (f_score, pos)
    heapq.heapify(open_set)
    
    came_from = {} # Menyimpan parent dari setiap node
    
    # g_score: Biaya dari start ke node
    g_score = { (x,y): float('inf') for x in range(game.width) for y in range(game.height) }
    g_score[start] = 0
    
    # f_score: Estimasi biaya dari start ke goal via node (g_score + heuristic)
    f_score = { (x,y): float('inf') for x in range(game.width) for y in range(game.height) }
    f_score[start] = heuristic_manhattan(start, goal)
    
    nodes_expanded = 0

    while open_set:
        nodes_expanded += 1
        _, current_pos = heapq.heappop(open_set)

        if current_pos == goal:
            # Rekonstruksi jalur
            path = []
            temp = current_pos
            while temp in came_from:
                path.append(temp)
                temp = came_from[temp]
            path.append(start)
            return path[::-1], nodes_expanded # Sukses (path dibalik)

        # Eksplorasi tetangga
        for neighbor in game.get_valid_neighbors(current_pos):
            # Biaya gerak antar tetangga selalu 1
            tentative_g_score = g_score[current_pos] + 1
            
            if tentative_g_score < g_score[neighbor]:
                # Jalur baru yang lebih baik ditemukan
                came_from[neighbor] = current_pos
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic_manhattan(neighbor, goal)
                
                if (f_score[neighbor], neighbor) not in open_set:
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return None, nodes_expanded # Gagal (tidak ada jalur)

def _run_bfs_simulation(game, start, goal, temp_obstacles):
    queue = deque([start])
    visited = {start}
    
    # Menambahkan semua rintangan simulasi ke 'visited'
    visited.update(temp_obstacles) 
    # Ekor adalah tujuan, jadi JANGAN anggap ekor sebagai rintangan
    if goal in visited:
        visited.remove(goal) 

    while queue:
        current_pos = queue.popleft()

        if current_pos == goal:
            return True # Sukses menemukan jalur ke ekor

        # Eksplorasi tetangga
        x, y = current_pos
        for dx, dy in [UP, DOWN, LEFT, RIGHT]:
            nx, ny = x + dx, y + dy
            new_pos = (nx, ny)
            
            # Cek dinding
            if 0 <= nx < game.width and 0 <= ny < game.height:
                if new_pos not in visited:
                    visited.add(new_pos)
                    queue.append(new_pos)
    
    return False # Gagal (tidak ada jalur ke ekor)


def is_path_safe(game, path_to_food):
    
    # 1. Buat tubuh ular hipotetis (virtual) menggunakan deque
    virtual_snake = deque(game.snake)
    virtual_snake_set = set(game.snake)
    
    # 2. Simulasikan pergerakan ular LANGKAH DEMI LANGKAH
    #    Kita tidak bisa hanya .add() karena ekor juga bergerak
    
    # path_to_food[0] adalah kepala saat ini, jadi kita mulai dari [1]
    for i in range(1, len(path_to_food)):
        new_head = path_to_food[i]
        
        # Tambahkan kepala baru
        virtual_snake.appendleft(new_head)
        virtual_snake_set.add(new_head)
        
        # Hapus ekor HANYA JIKA langkah ini BUKAN langkah memakan makanan
        if i < len(path_to_food) - 1: # Jika ini bukan langkah terakhir (ke makanan)
            tail = virtual_snake.pop()
            # Hati-hati: jangan hapus segmen tubuh jika ia muncul 2x
            # (ini jarang terjadi tapi mungkin, misal kepala memotong ekor)
            if tail not in virtual_snake:
                virtual_snake_set.remove(tail)
                
    # 3. Tentukan kepala dan ekor baru (hipotetis)
    final_head = virtual_snake[0] # Ini adalah posisi makanan
    final_tail = virtual_snake[-1]
    
    # 4. Jalankan simulasi BFS
    # Rintangan adalah tubuh ular virtual + rintangan game
    all_temp_obstacles = virtual_snake_set.union(game.static_obstacles, game.dynamic_obstacles)

    return _run_bfs_simulation(game, final_head, final_tail, all_temp_obstacles)

def get_direction_from_path(head, next_step):
    """Mendapatkan vektor arah (dx, dy) dari dua titik."""
    dx = next_step[0] - head[0]
    dy = next_step[1] - head[1]
    return (dx, dy)

def draw_game(screen, game, block_size):
    
    screen.fill(COLOR_BLACK) # Latar belakang
    
    # Gambar Rintangan Statis
    for (x, y) in game.static_obstacles:
        rect = pygame.Rect(x * block_size + W_PAD, y * block_size + H_PAD, 
                           block_size, block_size)
        pygame.draw.rect(screen, COLOR_GRAY, rect)
        
    # Gambar Rintangan Dinamis
    for (x, y) in game.dynamic_obstacles:
        rect = pygame.Rect(x * block_size + W_PAD, y * block_size + H_PAD, 
                           block_size, block_size)
        pygame.draw.rect(screen, COLOR_GRAY_DYNAMIC, rect)

    # Gambar Makanan
    if game.food:
        (x, y) = game.food
        rect = pygame.Rect(x * block_size + W_PAD, y * block_size + H_PAD, 
                           block_size, block_size)
        pygame.draw.rect(screen, COLOR_RED, rect)
        
    # Gambar Tubuh Ular
    for (x, y) in list(game.snake)[1:]:
        rect = pygame.Rect(x * block_size + W_PAD, y * block_size + H_PAD, 
                           block_size, block_size)
        pygame.draw.rect(screen, COLOR_GREEN, rect)
        pygame.draw.rect(screen, COLOR_GREEN_DARK, rect, 1) # Border

    # Gambar Kepala Ular
    (x, y) = game.snake[0]
    rect = pygame.Rect(x * block_size + W_PAD, y * block_size + H_PAD, 
                       block_size, block_size)
    pygame.draw.rect(screen, COLOR_GREEN_DARK, rect)
    
def run_simulation(LEVEL, ALGO, config, game_speed_fps=30):
    
    # 1. Inisialisasi Game Logic
    W, H = config[LEVEL]["size"]
    OBSTACLES = config[LEVEL]["obstacles"]
    FOOD_TRIGGER = config[LEVEL]["food_trigger"]
    SPAWN_COUNT = config[LEVEL]["obstacle_spawn_count"]
    game = SnakeGame(W, H, OBSTACLES, food_trigger=FOOD_TRIGGER, obstacle_spawn_count=SPAWN_COUNT)

    # 2. Inisialisasi Pygame
    pygame.init()
    SCREEN_WIDTH = W * BLOCK_SIZE + (W_PAD * 2)
    SCREEN_HEIGHT = H * BLOCK_SIZE + (H_PAD * 2)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(f"Snake Pathfinding - {ALGO} on {LEVEL} Level")
    clock = pygame.time.Clock()

    # Variabel untuk metrik
    total_decision_time = 0
    total_nodes_expanded = 0
    decision_count = 0
    
    # 3. Eksekusi Simulasi
    running = True
    current_path_deque = deque()

    while running and not game.game_over:
        
        # 3a. Event Handling (untuk tombol close darurat)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                game.game_over = True # Paksa game over
                game.game_over_reason = "User Interruption"
        
        # 3b. Algoritma mencari jalur (Logika BARU dengan Safe-Path Check HANYA UNTUK A*)
        if not current_path_deque:
            nodes_expanded = 0
            start_time = time.perf_counter()
            
            # --- LOGIKA BERCABANG BERDASARKAN ALGORITMA ---
            
            if ALGO == "A*":
                # --- LOGIKA A* (Dengan Safe-Path Check) ---
                path_to_food = None
                path_to_food, nodes = find_path_a_star(game, game.food)
                nodes_expanded += nodes
                
                safe_path_found = False
                if path_to_food:
                    # 2. Cek keamanan
                    if is_path_safe(game, path_to_food):
                        current_path_deque = deque(path_to_food[1:])
                        safe_path_found = True
                    else:
                        game.game_over_reason = "Dead-End Trap (Path Unsafe)"
                
                # 3. Jika tidak aman / tidak ada jalur, cari ekor
                if not safe_path_found:
                    path_to_tail = None
                    path_to_tail, nodes = find_path_a_star(game, game.snake[-1])
                    nodes_expanded += nodes
                    
                    if path_to_tail:
                        current_path_deque = deque(path_to_tail[1:])
                    else:
                        game.game_over = True
                        if not path_to_food and game.game_over_reason == "":
                            game.game_over_reason = "No Path Found (Trapped)"
            
            elif ALGO == "BFS":
                # --- LOGIKA BFS (Tanpa safe-path check) ---
                path_to_food = None
                path_to_food, nodes = find_path_bfs(game, game.food)
                nodes_expanded += nodes

                if path_to_food:
                    # BFS tidak peduli keamanan. Jika ada jalur, ambil.
                    current_path_deque = deque(path_to_food[1:])
                else:
                    # Jika tidak ada jalur ke makanan, BFS gagal.
                    game.game_over = True
                    game.game_over_reason = "No Path Found (Trapped)"
            
            end_time = time.perf_counter()
            total_decision_time += (end_time - start_time)
            total_nodes_expanded += nodes_expanded
            decision_count += 1
            
        # 3c. Ular bergerak mengikuti path
        if current_path_deque:
            next_step = current_path_deque.popleft()
            direction = get_direction_from_path(game.snake[0], next_step)
            game.move(direction)
            
            if game.game_over_reason == "Hit Dynamic Obstacle":
                current_path_deque.clear()
                game.game_over = False
                game.game_over_reason = ""
                
        elif not game.game_over:
            game.game_over = True
            game.game_over_reason = "Pathfinding Logic Error"
            
        # 3d. Drawing (Menggambar ke layar)
        draw_game(screen, game, BLOCK_SIZE)
        
        # 3e. Update Display
        pygame.display.flip()
        
        # 3f. Kontrol Kecepatan Game (Gunakan FPS tinggi untuk batch)
        clock.tick(game_speed_fps) 

    # 4. Tampilkan Hasil
    print(f" Selesai. Makanan: {game.score:<3} | Langkah: {game.steps:<4} | Alasan: {game.game_over_reason}")
    
    # Inisialisasi metrik
    avg_time = 0.0
    avg_expansion = 0.0
    
    if decision_count > 0:
        avg_time = (total_decision_time / decision_count) * 1000 # dalam ms
        avg_expansion = total_nodes_expanded / decision_count

    # 5. Pencatatan Data ke CSV
    log_file = 'snake_experiment_log.csv'
    file_exists = os.path.isfile(log_file)
    header = ['Algorithm', 'Level', 'Total Food', 'Total Steps', 
              'Average Time (ms)', 'Average Expansion', 'Replans', 'Game Over Reason']
    data_row = [ALGO, LEVEL, game.score, game.steps, f"{avg_time:.4f}",
                f"{avg_expansion:.2f}", decision_count, game.game_over_reason]

    try:
        with open(log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(header)
            writer.writerow(data_row)
    except IOError as e:
        print(f"\n[ERROR] Gagal mencatat data ke CSV: {e}")
    
    # 6. Tampilkan Layar "Game Over"
    font = pygame.font.SysFont(None, 40)
    text_str = f"GAME OVER: {game.game_over_reason}"
    text = font.render(text_str, True, COLOR_WHITE)
    text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
    screen.blit(text, text_rect)
    pygame.display.flip()
    
    pygame.time.wait(250) 
    pygame.quit()

def analyze_results(log_file):
    if not os.path.isfile(log_file):
        print(f"File log '{log_file}' tidak ditemukan. Tidak ada analisis.")
        return

    # --- 1. Agregasi Data ---
    # Struktur Data: stats_raw[LEVEL][ALGO][METRIC] = [list of values]
    stats_raw = collections.defaultdict(lambda: 
                    collections.defaultdict(lambda: 
                        collections.defaultdict(list)))
    
    # Struktur Data: stats_raw_global[ALGO][METRIC] = [list of values]
    stats_raw_global = collections.defaultdict(lambda: collections.defaultdict(list))
    
    all_levels_found = set()

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
                
                level = cleaned_row.get('Level')
                algo = cleaned_row.get('Algorithm')
                
                if not level or not algo:
                    print(f"Peringatan: Melewatkan baris data tidak lengkap: {cleaned_row}")
                    continue
                    
                all_levels_found.add(level)
                
                try:
                    metrics_data = {
                        'Total Food': int(cleaned_row['Total Food']),
                        'Total Steps': int(cleaned_row['Total Steps']),
                        'Average Time (ms)': float(cleaned_row['Average Time (ms)']),
                        'Average Expansion': float(cleaned_row['Average Expansion']),
                        'Replans': int(cleaned_row['Replans'])
                    }
                    
                    for metric, value in metrics_data.items():
                        stats_raw[level][algo][metric].append(value)
                        stats_raw_global[algo][metric].append(value)
                        
                except ValueError as e:
                    print(f"Peringatan: Melewatkan baris data error: {e} | {cleaned_row}")

        if not stats_raw:
            print(f"Tidak ada data valid yang ditemukan di {log_file}.")
            return

        # --- 2. Fungsi Normalisasi (Tetap sama) ---
        def normalize(val_bfs, val_astar, bigger_is_better=True):
            x_min = min(val_bfs, val_astar)
            x_max = max(val_bfs, val_astar)
            if x_max == x_min: return (1.0, 1.0)
            n_bfs = (val_bfs - x_min) / (x_max - x_min)
            n_astar = (val_astar - x_min) / (x_max - x_min)
            return (n_bfs, n_astar) if bigger_is_better else (1.0 - n_bfs, 1.0 - n_astar)

        def normalize_rei(val_bfs, val_astar):
            x_max = max(val_bfs, val_astar, 1)
            if x_max == 0: return (1.0, 1.0)
            return (1.0 - (val_bfs / x_max), 1.0 - (val_astar / x_max))

        # --- 3. Definisikan SEMUA Bobot ---
        all_weights = {
            'Global': {'Food': 0.35, 'Steps': 0.10, 'Time': 0.25, 'Exp': 0.15, 'REI': 0.15},
            
            'Easy':   {
                'Food': 0.10, 
                'Steps': 0.30, 
                'Time': 0.40, 
                'Exp': 0.10,
                'REI': 0.10
            }, 
            
            'Medium': {
                'Food': 0.40, 
                'Steps': 0.15,
                'Time': 0.15, 
                'Exp': 0.15,   
                'REI': 0.15
            },
            'Hard':   {
                'Food': 0.45, 
                'Steps': 0.05, 
                'Time': 0.10,  
                'Exp': 0.25, 
                'REI': 0.15
            }
        }

        # --- 4. Fungsi Helper untuk Menghitung Skor ---
        def calculate_score(raw_data_bfs, raw_data_astar, formula_weights):
            # Hitung rata-rata
            avg_bfs = {metric: sum(vals) / len(vals) for metric, vals in raw_data_bfs.items() if vals}
            avg_astar = {metric: sum(vals) / len(vals) for metric, vals in raw_data_astar.items() if vals}
            
            # Ambil nilai rata-rata (default 0)
            bfs_food  = avg_bfs.get('Total Food', 0)
            bfs_steps = avg_bfs.get('Total Steps', 0)
            bfs_time  = avg_bfs.get('Average Time (ms)', 0)
            bfs_exp   = avg_bfs.get('Average Expansion', 0)
            bfs_rei   = avg_bfs.get('Replans', 0)
            
            astar_food  = avg_astar.get('Total Food', 0)
            astar_steps = avg_astar.get('Total Steps', 0)
            astar_time  = avg_astar.get('Average Time (ms)', 0)
            astar_exp   = avg_astar.get('Average Expansion', 0)
            astar_rei   = avg_astar.get('Replans', 0)

            # Normalisasi
            (n_bfs_food, n_astar_food)   = normalize(bfs_food, astar_food, bigger_is_better=True)
            (n_bfs_steps, n_astar_steps) = normalize(bfs_steps, astar_steps, bigger_is_better=False)
            (n_bfs_time, n_astar_time)   = normalize(bfs_time, astar_time, bigger_is_better=False)
            (n_bfs_exp, n_astar_exp)     = normalize(bfs_exp, astar_exp, bigger_is_better=False)
            (n_bfs_rei, n_astar_rei)     = normalize_rei(bfs_rei, astar_rei)
            
            n_scores_bfs = {'Food': n_bfs_food, 'Steps': n_bfs_steps, 'Time': n_bfs_time, 'Exp': n_bfs_exp, 'REI': n_bfs_rei}
            n_scores_astar = {'Food': n_astar_food, 'Steps': n_astar_steps, 'Time': n_astar_time, 'Exp': n_astar_exp, 'REI': n_astar_rei}

            # Hitung skor akhir
            final_score_bfs = 0
            final_score_astar = 0
            for metric, weight in formula_weights.items():
                final_score_bfs += n_scores_bfs[metric] * weight
                final_score_astar += n_scores_astar[metric] * weight
            
            return final_score_bfs, final_score_astar

        # --- 5. Jalankan Analisis Per-Level ---
        print("\n" + "="*50)
        print(" HASIL ANALISIS PER-LEVEL ".center(50, "="))
        print("="*50)

        for level in sorted(all_levels_found):
            print(f"\n--- Analisis Level: {level} ---")
            
            raw_data_bfs = stats_raw.get(level, {}).get('BFS', {})
            raw_data_astar = stats_raw.get(level, {}).get('A*', {})
            
            if not raw_data_bfs or not raw_data_astar:
                print(f"Data tidak lengkap untuk level {level}. Melewatkan.")
                continue

            # Ambil formula skor yang sesuai
            formula_weights = all_weights.get(level, all_weights['Global'])
            score_bfs, score_astar = calculate_score(raw_data_bfs, raw_data_astar, formula_weights)
            
            print(f"{'Algorithm':<10} | {'Skor Akhir':>12}")
            print("-" * 25)
            print(f"{'A*':<10} | {score_astar:>12.3f}")
            print(f"{'BFS':<10} | {score_bfs:>12.3f}")
            
            if score_astar > score_bfs:
                print(f"Pemenang: A* (Skor {score_astar:.3f} vs {score_bfs:.3f})")
            elif score_bfs > score_astar:
                print(f"Pemenang: BFS (Skor {score_bfs:.3f} vs {score_astar:.3f})")
            else:
                print(f"Pemenang: Seri (Skor {score_bfs:.3f})")

        # --- 6. Jalankan Analisis Global ---
        print("\n" + "="*50)
        print(" HASIL ANALISIS GLOBAL (SEMUA LEVEL) ".center(50, "="))
        print("="*50)
        
        raw_global_bfs = stats_raw_global.get('BFS', {})
        raw_global_astar = stats_raw_global.get('A*', {})
        
        if not raw_global_bfs or not raw_global_astar:
            print("Data global tidak lengkap. Analisis global dibatalkan.")
            return

        # Hitung skor global menggunakan formula "Global"
        formula_weights_global = all_weights['Global']
        score_global_bfs, score_global_astar = calculate_score(raw_global_bfs, raw_global_astar, formula_weights_global)

        print("\nSkor Rata-rata Gabungan (Formula Global):")
        print(f"{'Algorithm':<10} | {'Skor Akhir':>12}")
        print("-" * 25)
        print(f"{'A*':<10} | {score_global_astar:>12.3f}")
        print(f"{'BFS':<10} | {score_global_bfs:>12.3f}")
        
        print("\n" + "🏆" * 20)
        print(" KESIMPULAN UTAMA ".center(40))
        if score_global_astar > score_global_bfs:
            print(f"Secara keseluruhan, A* lebih unggul (Skor {score_global_astar:.3f} vs {score_global_bfs:.3f}).")
        elif score_global_bfs > score_global_astar:
             print(f"Secara keseluruhan, BFS lebih unggul (Skor {score_global_bfs:.3f} vs {score_global_astar:.3f}).")
        else:
             print(f"Secara keseluruhan, A* dan BFS memiliki performa seimbang.")
        print("=" * 50)

    except Exception as e:
        print(f"Gagal menganalisis file CSV: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    
    # --- Konfigurasi Skenario ---
    valid_levels = ["Easy", "Medium", "Hard"]
    while True:
        level_input = input(f"Pilih Level Eksperimen ({'/'.join(valid_levels)}): ").capitalize()
        if level_input in valid_levels:
            LEVEL = level_input
            break
        print(f"Input tidak valid. Harap pilih salah satu dari: {', '.join(valid_levels)}")
    
    COLOR_GRAY = (100, 100, 100)
    COLOR_GRAY_DYNAMIC = (160, 160, 160)

    # --- Persiapan Lingkungan Level ---
    
    # Level Easy: Tanpa obstacle
    W_easy, H_easy = 15, 15
    obs_easy = set()

    # Level Medium: Dua Pilar Vertikal
    obs_medium = set()
    x_kiri, x_kanan = 6, 13
    y_start, y_end = 5, 14
    for i in range(y_start, y_end + 1):
        obs_medium.add((x_kiri, i))
        obs_medium.add((x_kanan, i))

    # Level Hard: Plus (+) shape, arm length 6
    obs_hard = set()
    center_h, arm_h = 12, 6
    obs_hard.add((center_h, center_h))
    for i in range(1, arm_h + 1):
        obs_hard.add((center_h, center_h - i))
        obs_hard.add((center_h, center_h + i))
        obs_hard.add((center_h - i, center_h))
        obs_hard.add((center_h + i, center_h))

    # --- Definisi Config ---
    config = {
        "Easy": {
            "size": (W_easy, H_easy),
            "obstacles": obs_easy,
            "food_trigger": 0,           # 0 = Nonaktif
            "obstacle_spawn_count": (0, 0)
        },
        "Medium": {
            "size": (20, 20),
            "obstacles": obs_medium,
            "food_trigger": 7,           # Setiap 7 makanan
            "obstacle_spawn_count": (1, 2)  # Spawn 1 SAMPAI 2 
        },
        "Hard": {
            "size": (25, 25),
            "obstacles": obs_hard,
            "food_trigger": 5,           # Setiap 5 makanan
            "obstacle_spawn_count": (1, 5)  # Spawn 1 SAMPAI 5 
        }
    }
    
    log_file_name = 'snake_experiment_log.csv'
    
    while True:
        print("\n" + "="*30)
        print(f"Menjalankan Batch (Level: {LEVEL})")
        print("="*30)
        print("Menjalankan 5x BFS...")
        for i in range(5):
            print(f"  [BFS Run {i+1}/5]...", end="")
            run_simulation(LEVEL, "BFS", config, game_speed_fps=70) 
        
        print("\nMenjalankan 5x A*...")
        for i in range(5):
            print(f"  [A* Run {i+1}/5]...", end="")
            run_simulation(LEVEL, "A*", config, game_speed_fps=70)
        
        print("="*30)
        
        # Checkpoint
        lanjut = ""
        while lanjut not in ['y', 'n']:
            lanjut = input("Batch 10 run selesai. Lanjut 10 run lagi? (y/n): ").lower()
        
        if lanjut == 'n':
            break
    
    print("\nSimulasi dihentikan oleh pengguna. Memulai analisis data...")
    analyze_results(log_file_name)
