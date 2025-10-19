import random
import heapq
from collections import deque
import time
import pygame
import csv  # <-- TAMBAHKAN INI
import os   # <-- TAMBAHKAN INI
import collections

# --- Konstanta Arah (opsional, untuk kejelasan) ---
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# --- Konstanta Pygame ---
BLOCK_SIZE = 20  # Ukuran setiap kotak grid dalam piksel
(W_PAD, H_PAD) = (0, 0) # Padding jika perlu

# Warna (R, G, B)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREEN = (0, 200, 0)
COLOR_GREEN_DARK = (0, 150, 0)
COLOR_RED = (200, 0, 0)
COLOR_GRAY = (100, 100, 100)

class SnakeGame:
    """
    Kelas ini mengelola semua logika inti dari permainan Snake.
    """
    def __init__(self, width, height, static_obstacles=None, food_trigger=0, obstacle_spawn_count=(0,0)):
        self.width = width
        self.height = height
        self.grid_size = (width, height)
        
        self.static_obstacles = set(static_obstacles) if static_obstacles else set()
        self.dynamic_obstacles = set() # <-- BARU: Set untuk obstacle dinamis
        
        # Konfigurasi obstacle dinamis
        self.food_trigger_threshold = food_trigger # <-- Ganti nama dari food_per_obstacle...
        self.obstacle_spawn_min = obstacle_spawn_count[0] # <-- BARU
        self.obstacle_spawn_max = obstacle_spawn_count[1] # <-- BARU
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
        """Menempatkan makanan di posisi acak yang valid."""
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            pos = (x, y)
            # Pastikan makanan tidak muncul di atas ular atau rintangan
            if (pos not in self.snake_body_set and
                pos not in self.static_obstacles and
                pos not in self.dynamic_obstacles): # <-- TAMBAHKAN PENGECEKAN INI
                
                self.food = pos
                return

    # --- METODE BARU ---
    def place_dynamic_obstacle(self):
        """
        Menempatkan rintangan dinamis di posisi acak yang valid.
        Mengembalikan True jika berhasil, False jika gagal (misal: papan penuh).
        """
        # Coba cari tempat kosong, tapi batasi jumlah percobaan (misal 50x)
        # Ini mencegah infinite loop jika papan penuh
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
        """Mendapatkan tetangga yang valid (tidak menabrak dinding/rintangan)."""
        neighbors = []
        x, y = pos
        for dx, dy in [UP, DOWN, LEFT, RIGHT]:
            nx, ny = x + dx, y + dy
            new_pos = (nx, ny)
            if 0 <= nx < self.width and 0 <= ny < self.height and \
               new_pos not in self.static_obstacles and \
               new_pos not in self.dynamic_obstacles: # <-- TAMBAHKAN PENGECEKAN INI
                
                if new_pos not in self.snake_body_set:
                     neighbors.append(new_pos)
                elif len(self.snake) > 2 and new_pos == self.snake[-1] and new_pos != self.food:
                 neighbors.append(new_pos)
        return neighbors

    def move(self, direction):
        """
        Menggerakkan ular ke arah yang ditentukan.
        """
        if self.game_over:
            return

        current_head = self.snake[0]
        dx, dy = direction
        new_head = (current_head[0] + dx, current_head[1] + dy)
        
        self.steps += 1

        # 1. Cek Game Over (Dinding, Rintangan, Self-collision)
        # --- PERBARUI BLOK INI ---
        if ( 
           (new_head in self.snake_body_set) or
           (new_head in self.static_obstacles) or
           (new_head in self.dynamic_obstacles) or # <-- Komentar sekarang aman
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
        # --- AKHIR PERBARUAN ---

        # 2. Tambahkan kepala baru
        self.snake.appendleft(new_head)
        self.snake_body_set.add(new_head)

        # 3. Cek Makanan
        # --- PERBARUI BLOK INI ---
        if new_head == self.food:
            self.score += 1
            # Penting: Panggil place_food() DULU sebelum obstacle,
            # agar obstacle tidak spawn di tempat food baru
            self.place_food() 
            
            # --- Logika Obstacle Dinamis ---
            if self.food_trigger_threshold > 0: # Cek jika fitur ini aktif
                self.food_eaten_counter += 1
                
                # Jika sudah mencapai threshold 'n'
                if self.food_eaten_counter >= self.food_trigger_threshold:
                    
                    # TENTUKAN JUMLAH OBSTACLE (SESUAI REQUEST ANDA)
                    num_to_spawn = random.randint(self.obstacle_spawn_min, self.obstacle_spawn_max)
                    
                    # Panggil fungsi spawn sebanyak num_to_spawn
                    for _ in range(num_to_spawn):
                        # Panggil place_dynamic_obstacle()
                        # Kita tambahkan cek (dari langkah 5) untuk keamanan
                        if not self.place_dynamic_obstacle():
                            # Gagal menempatkan (papan penuh), hentikan spawn
                            break 
                            
                    self.food_eaten_counter = 0 # Reset counter
            # --- Akhir Logika ---
            
        else:
            # Hapus ekor (ular bergerak)
            tail = self.snake.pop()
            self.snake_body_set.remove(tail)
        # --- AKHIR PERBARUAN ---


# --- ALGORITMA PATHFINDING ---

def heuristic_manhattan(a, b):
    """Menghitung jarak Manhattan antara dua titik."""
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)

def find_path_bfs(game, goal):
    """
    Mencari jalur dari kepala ular ke makanan menggunakan BFS.
    Menjamin jalur terpendek.
    """
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
    """
    Mencari jalur dari kepala ular ke makanan menggunakan A*.
    Menggunakan heuristik Manhattan.
    """
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
    """Helper BFS internal untuk simulasi. Menghindari tubuh ular palsu."""
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
    """
    Mensimulasikan pergerakan ular di 'path_to_food' dan mengecek
    apakah ada jalur dari kepala baru ke ekor baru.
    """
    
    # 1. Buat tubuh ular hipotetis setelah bergerak & makan
    temp_snake_body = set(game.snake_body_set)
    
    # 'Makan' semua sel di jalur
    for pos in path_to_food[1:]: # Mulai dari [1:] karena [0] sudah di tubuh
        temp_snake_body.add(pos)
        
    # Karena kita 'makan', ekor TIDAK bergerak/dihapus.
    
    # 2. Tentukan kepala dan ekor baru (hipotetis)
    new_head = path_to_food[-1] # Posisi kepala adalah di makanan
    new_tail = game.snake[-1]   # Ekor tetap di tempat
    
    # 3. Jalankan simulasi BFS
    # Kita harus menggabungkan semua rintangan
    all_temp_obstacles = temp_snake_body.union(game.static_obstacles, game.dynamic_obstacles)

    return _run_bfs_simulation(game, new_head, new_tail, all_temp_obstacles)

def get_direction_from_path(head, next_step):
    """Mendapatkan vektor arah (dx, dy) dari dua titik."""
    dx = next_step[0] - head[0]
    dy = next_step[1] - head[1]
    return (dx, dy)

def draw_game(screen, game, block_size):
    """Fungsi helper untuk menggambar state game di layar Pygame."""
    
    screen.fill(COLOR_BLACK) # Latar belakang
    
    # Gambar Rintangan Statis
    for (x, y) in game.static_obstacles:
        rect = pygame.Rect(x * block_size + W_PAD, y * block_size + H_PAD, 
                           block_size, block_size)
        pygame.draw.rect(screen, COLOR_GRAY, rect)
        
    # --- BLOK BARU ---
    # Gambar Rintangan Dinamis
    for (x, y) in game.dynamic_obstacles:
        rect = pygame.Rect(x * block_size + W_PAD, y * block_size + H_PAD, 
                           block_size, block_size)
        pygame.draw.rect(screen, COLOR_GRAY_DYNAMIC, rect) # Gunakan warna baru
    # --- AKHIR BLOK BARU ---

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
    pygame.draw.rect(screen, COLOR_GREEN_DARK, rect) # Kepala warna lebih gelap
    # ... (sisa fungsi ini tidak berubah) ...
    
def run_simulation(LEVEL, ALGO, config, game_speed_fps=30):
    """
    Menjalankan satu simulasi penuh dari awal sampai akhir,
    mencatat hasilnya ke CSV, dan menutup Pygame secara otomatis.
    """
    
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
    
    # 3. Eksekusi Simulasi (Game Loop Utama)
    running = True
    current_path_deque = deque()

    while running and not game.game_over:
        
        # 3a. Event Handling (Hanya untuk tombol close darurat)
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
                # --- LOGIKA PINTAR A* (Dengan Safe-Path Check) ---
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
                # --- LOGIKA NAIF BFS (Tanpa Safe-Path Check) ---
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

    # 4. Tampilkan Hasil (di Konsol) - Versi singkat
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
    
    # 6. Tampilkan Layar "Game Over" (VERSI OTOMATIS)
    font = pygame.font.SysFont(None, 40)
    text_str = f"GAME OVER: {game.game_over_reason}"
    text = font.render(text_str, True, COLOR_WHITE)
    text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
    screen.blit(text, text_rect)
    pygame.display.flip()
    
    pygame.time.wait(250) # <-- TUNGGU HANYA 250ms
    pygame.quit() # <-- TUTUP OTOMATIS
# --- MAIN LOOP (Contoh Eksekusi) ---

def analyze_results(log_file, level_to_analyze):
    """
    Membaca seluruh file log CSV dan membuat kesimpulan
    performa BFS vs A* untuk level yang ditentukan menggunakan
    model skoring berbobot (weighted scoring model).
    """
    if not os.path.isfile(log_file):
        print(f"File log '{log_file}' tidak ditemukan. Tidak ada analisis.")
        return

    # --- 1. Agregasi Data ---
    # Kumpulkan semua data mentah dari CSV
    stats_raw = collections.defaultdict(lambda: collections.defaultdict(list))
    total_runs = collections.defaultdict(int)

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
                
                if cleaned_row['Level'] == level_to_analyze:
                    algo = cleaned_row['Algorithm']
                    total_runs[algo] += 1
                    try:
                        stats_raw[algo]['Total Food'].append(int(cleaned_row['Total Food']))
                        stats_raw[algo]['Total Steps'].append(int(cleaned_row['Total Steps']))
                        stats_raw[algo]['Average Time (ms)'].append(float(cleaned_row['Average Time (ms)']))
                        stats_raw[algo]['Average Expansion'].append(float(cleaned_row['Average Expansion']))
                        stats_raw[algo]['Replans'].append(int(cleaned_row['Replans']))
                    except ValueError as e:
                        print(f"Peringatan: Melewatkan baris data error: {e} | {cleaned_row}")

        if not stats_raw:
            print(f"Tidak ada data ditemukan untuk Level '{level_to_analyze}' di {log_file}.")
            return

        # Hitung Rata-rata (mean) dari data mentah
        avg_stats = collections.defaultdict(dict)
        for algo, metrics in stats_raw.items():
            for metric, values in metrics.items():
                avg_stats[algo][metric] = sum(values) / len(values) if values else 0
        
        # Siapkan data mentah (rata-rata) untuk normalisasi
        raw_bfs = avg_stats.get('BFS', {})
        raw_astar = avg_stats.get('A*', {})

        # --- 2. Fungsi Normalisasi ---
        def normalize(val_bfs, val_astar, bigger_is_better=True):
            """Normalisasi Min-Max untuk dua nilai."""
            x_min = min(val_bfs, val_astar)
            x_max = max(val_bfs, val_astar)
            
            # Hindari pembagian dengan nol jika nilainya identik
            if x_max == x_min:
                return (1.0, 1.0) # Keduanya sama baiknya
                
            n_bfs = (val_bfs - x_min) / (x_max - x_min)
            n_astar = (val_astar - x_min) / (x_max - x_min)
            
            if bigger_is_better:
                return (n_bfs, n_astar)
            else: # Smaller is better, invert scores
                return (1.0 - n_bfs, 1.0 - n_astar)

        def normalize_rei(val_bfs, val_astar):
            """Normalisasi khusus REI: 1 - (x / max(x))"""
            x_max = max(val_bfs, val_astar, 1) # Gunakan 1 untuk hindari /0
            if x_max == 0:
                return (1.0, 1.0) # Keduanya sempurna (tidak ada replan)
                
            n_bfs = 1.0 - (val_bfs / x_max)
            n_astar = 1.0 - (val_astar / x_max)
            return (n_bfs, n_astar)

        # --- 3. Dapatkan Skor Ternormalisasi (N_scores) ---
        
        # Ambil nilai rata-rata (default ke 0 jika tidak ada data)
        bfs_food  = raw_bfs.get('Total Food', 0)
        bfs_steps = raw_bfs.get('Total Steps', 0)
        bfs_time  = raw_bfs.get('Average Time (ms)', 0)
        bfs_exp   = raw_bfs.get('Average Expansion', 0)
        bfs_rei   = raw_bfs.get('Replans', 0)
        
        astar_food  = raw_astar.get('Total Food', 0)
        astar_steps = raw_astar.get('Total Steps', 0)
        astar_time  = raw_astar.get('Average Time (ms)', 0)
        astar_exp   = raw_astar.get('Average Expansion', 0)
        astar_rei   = raw_astar.get('Replans', 0)

        # Lakukan Normalisasi
        (n_bfs_food, n_astar_food)   = normalize(bfs_food, astar_food, bigger_is_better=True)
        (n_bfs_steps, n_astar_steps) = normalize(bfs_steps, astar_steps, bigger_is_better=False)
        (n_bfs_time, n_astar_time)   = normalize(bfs_time, astar_time, bigger_is_better=False)
        (n_bfs_exp, n_astar_exp)     = normalize(bfs_exp, astar_exp, bigger_is_better=False)
        (n_bfs_rei, n_astar_rei)     = normalize_rei(bfs_rei, astar_rei)
        
        # Kumpulkan N-scores dalam dictionary
        n_scores_bfs = {'Food': n_bfs_food, 'Steps': n_bfs_steps, 'Time': n_bfs_time, 'Exp': n_bfs_exp, 'REI': n_bfs_rei}
        n_scores_astar = {'Food': n_astar_food, 'Steps': n_astar_steps, 'Time': n_astar_time, 'Exp': n_astar_exp, 'REI': n_astar_rei}

        # --- 4. Terapkan Bobot (Weights) ---
        weights = {
            'Global': {'Food': 0.35, 'Steps': 0.10, 'Time': 0.25, 'Exp': 0.15, 'REI': 0.15},
            'Easy':   {'Food': 0.30, 'Steps': 0.25, 'Time': 0.15, 'Exp': 0.10, 'REI': 0.20},
            'Medium': {'Food': 0.30, 'Steps': 0.15, 'Time': 0.20, 'Exp': 0.10, 'REI': 0.25},
            'Hard':   {'Food': 0.25, 'Steps': 0.10, 'Time': 0.25, 'Exp': 0.10, 'REI': 0.30}
        }
        
        final_scores = {'BFS': {}, 'A*': {}}
        for formula_name, formula_weights in weights.items():
            score_bfs = 0
            score_astar = 0
            for metric, weight in formula_weights.items():
                score_bfs += n_scores_bfs[metric] * weight
                score_astar += n_scores_astar[metric] * weight
            final_scores['BFS'][formula_name] = score_bfs
            final_scores['A*'][formula_name] = score_astar

        # --- 5. Tampilkan Kesimpulan Baru ---
        
        # Tabel 1: Rata-rata Mentah (untuk konteks)
        print("\n" + "="*48)
        print(f" RATA-RATA MENTAH (Level: {level_to_analyze}) ".center(48, "="))
        print("="*48)
        print(f"{'Metrik':<20} | {'BFS':>12} | {'A*':>12}")
        print("-" * 49)
        print(f"{'Total Food':<20} | {bfs_food:>12.2f} | {astar_food:>12.2f}")
        print(f"{'Total Steps':<20} | {bfs_steps:>12.2f} | {astar_steps:>12.2f}")
        print(f"{'Average Time (ms)':<20} | {bfs_time:>12.2f} | {astar_time:>12.2f}")
        print(f"{'Average Expansion':<20} | {bfs_exp:>12.2f} | {astar_exp:>12.2f}")
        print(f"{'Replans':<20} | {bfs_rei:>12.2f} | {astar_rei:>12.2f}")
        print(f"\nTotal Runs: {total_runs.get('BFS', 0)} (BFS), {total_runs.get('A*', 0)} (A*)")

        # Tabel 2: Skor Akhir (Hasil Utama)
        print("\n" + "="*48)
        print(f" SKOR AKHIR TERNORMALISASI ".center(48, "="))
        print("="*48)
        print(f"{'Formula Skor':<20} | {'BFS':>12} | {'A*':>12} | {'Pemenang':<8}")
        print("-" * 49)
        
        for formula_name in weights.keys():
            bfs_score = final_scores['BFS'][formula_name]
            astar_score = final_scores['A*'][formula_name]
            winner = "A*" if astar_score > bfs_score else "BFS" if bfs_score > astar_score else "Seri"
            print(f"{formula_name:<20} | {bfs_score:>12.3f} | {astar_score:>12.3f} | {winner:<8}")
        
        print("=" * 49)

        # Kesimpulan Final berdasarkan formula spesifik level tersebut
        level_specific_score_bfs = final_scores['BFS'][level_to_analyze]
        level_specific_score_astar = final_scores['A*'][level_to_analyze]
        
        print(f"\n🏆 KESIMPULAN (Formula Level: {level_to_analyze}):")
        if level_specific_score_astar > level_specific_score_bfs:
            print(f"A* lebih unggul dengan skor {level_specific_score_astar:.3f} vs {level_specific_score_bfs:.3f}.")
        elif level_specific_score_bfs > level_specific_score_astar:
             print(f"BFS lebih unggul dengan skor {level_specific_score_bfs:.3f} vs {level_specific_score_astar:.3f}.")
        else:
             print(f"A* dan BFS memiliki performa seimbang dengan skor {level_specific_score_bfs:.3f}.")
        print("=" * 49)

    except Exception as e:
        print(f"Gagal menganalisis file CSV: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    
    # --- Konfigurasi Skenario (Hanya tanya LEVEL) ---
    valid_levels = ["Easy", "Medium", "Hard"]
    while True:
        level_input = input(f"Pilih Level Eksperimen ({'/'.join(valid_levels)}): ").capitalize()
        if level_input in valid_levels:
            LEVEL = level_input
            break
        print(f"Input tidak valid. Harap pilih salah satu dari: {', '.join(valid_levels)}")

    # GAME_SPEED_FPS diatur di dalam run_simulation (misal: 500)
    # ALGO akan di-loop
    
    COLOR_GRAY = (100, 100, 100)
    COLOR_GRAY_DYNAMIC = (160, 160, 160) # Warna baru untuk obstacle dinamis

    # --- Persiapan Obstacle Statis ---
    
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
            "obstacle_spawn_count": (1, 1)  # Spawn TEPAT 1
        },
        "Hard": {
            "size": (25, 25),
            "obstacles": obs_hard,
            "food_trigger": 5,           # Setiap 5 makanan
            "obstacle_spawn_count": (1, 5)  # Spawn 1 SAMPAI 5 (Random)
        }
    }
    
    # --- (BARU) Main Execution Loop ---
    log_file_name = 'snake_experiment_log.csv'
    
    while True:
        print("\n" + "="*30)
        print(f"Menjalankan Batch (Level: {LEVEL})")
        print("="*30)
        print("Menjalankan 5x BFS...")
        for i in range(5):
            print(f"  [BFS Run {i+1}/5]...", end="")
            # Gunakan FPS tinggi (misal 500) untuk simulasi cepat
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
    
    # --- (BARU) Analisis Final ---
    print("\nSimulasi dihentikan oleh pengguna. Memulai analisis data...")
    analyze_results(log_file_name, LEVEL)
