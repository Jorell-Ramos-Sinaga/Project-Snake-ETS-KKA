import random
import heapq
from collections import deque
import time
import pygame

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
    def __init__(self, width, height, static_obstacles=None, food_per_obstacle=0): # <-- Tambah param
        self.width = width
        self.height = height
        self.grid_size = (width, height)
        
        self.static_obstacles = set(static_obstacles) if static_obstacles else set()
        self.dynamic_obstacles = set() # <-- BARU: Set untuk obstacle dinamis
        
        # Konfigurasi obstacle dinamis
        self.food_per_obstacle_threshold = food_per_obstacle # <-- BARU: Nilai 'n'
        self.food_eaten_counter = 0 # <-- BARU: Penghitung makanan
        
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
        """Menempatkan rintangan dinamis di posisi acak yang valid."""
        # Terus mencari posisi sampai ketemu yang valid
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            pos = (x, y)
            
            # Pastikan tidak spawn di atas ular, makanan, atau obstacle lain
            if pos not in self.snake_body_set and \
               pos not in self.static_obstacles and \
               pos not in self.dynamic_obstacles and \
               pos != self.food:
                
                self.dynamic_obstacles.add(pos)
                return # Keluar dari loop jika berhasil

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
                elif new_pos == self.snake[-1] and new_pos != self.food:
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
            if self.food_per_obstacle_threshold > 0: # Cek jika fitur ini aktif
                self.food_eaten_counter += 1
                # Jika sudah mencapai threshold 'n'
                if self.food_eaten_counter >= self.food_per_obstacle_threshold:
                    self.place_dynamic_obstacle()
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
    

# --- MAIN LOOP (Contoh Eksekusi) ---

if __name__ == "__main__":
    
    # --- Konfigurasi Skenario (sesuai proposal) ---
    valid_levels = ["Easy", "Medium", "Hard"]
    while True:
        level_input = input(f"Pilih Level ({'/'.join(valid_levels)}): ").capitalize()
        if level_input in valid_levels:
            LEVEL = level_input
            break
        print(f"Input tidak valid. Harap pilih salah satu dari: {', '.join(valid_levels)}")

    valid_algos = ["BFS", "A*"]
    while True:
        # .upper() dan .replace() untuk menangani input seperti "a*", "a *", atau "bfs"
        algo_input = input(f"Pilih Algoritma ({'/'.join(valid_algos)}): ").upper().replace(" ", "")
        if algo_input in valid_algos:
            ALGO = algo_input
            break
        print(f"Input tidak valid. Harap pilih salah satu dari: {', '.join(valid_algos)}")
    GAME_SPEED_FPS = 10 # Seberapa cepat game berjalan
    
    COLOR_GRAY = (100, 100, 100)
    COLOR_GRAY_DYNAMIC = (160, 160, 160) # Warna baru untuk obstacle dinamis

    # --- Persiapan Obstacle Statis ---
    
    # Level Easy: L-shape di 4 sudut
    obs_easy = set()
    W_easy, H_easy = 15, 15
    # Bentuk 'L' dasar di pojok kiri atas
    base_shape_easy = [(3,3), (3,4), (4,3)] 
    
    for x, y in base_shape_easy:
        obs_easy.add((x, y))                     # Top-Left (Asli)
        obs_easy.add((W_easy - 1 - x, y))        # Top-Right (Mirror X)
        obs_easy.add((x, H_easy - 1 - y))        # Bottom-Left (Mirror Y)
        obs_easy.add((W_easy - 1 - x, H_easy - 1 - y)) # Bottom-Right (Mirror X, Y)

    # Level Medium: Dua Pilar Vertikal
    obs_medium = set()
    
    # Tentukan posisi X pilar (simetris di sekitar 9.5)
    x_kiri = 6
    x_kanan = 13  # (karena 19 - 6 = 13)
    
    # Tentukan panjang pilar
    y_start, y_end = 5, 14 # Panjang 10 blok
    
    for i in range(y_start, y_end + 1):
        obs_medium.add((x_kiri, i))   # Pilar kiri
        obs_medium.add((x_kanan, i))  # Pilar kanan

    # Level Hard: Plus (+) shape, arm length 6
    obs_hard = set()
    center_h, arm_h = 12, 6 # (center 12 untuk grid 25x25)
    obs_hard.add((center_h, center_h)) # Titik tengah
    for i in range(1, arm_h + 1):
        obs_hard.add((center_h, center_h - i)) # Lengan atas
        obs_hard.add((center_h, center_h + i)) # Lengan bawah
        obs_hard.add((center_h - i, center_h)) # Lengan kiri
        obs_hard.add((center_h + i, center_h)) # Lengan kanan

    # --- Definisi Config ---
    # GANTI dictionary 'config' Anda yang lama dengan yang ini
    config = {
        "Easy": {
            "size": (W_easy, H_easy),
            "obstacles": obs_easy,
            "food_per_obstacle": 0 # 0 = Nonaktif
        },
        "Medium": {
            "size": (20, 20),
            "obstacles": obs_medium,
            "food_per_obstacle": 7 
        },
        "Hard": {
            "size": (25, 25),
            "obstacles": obs_hard,
            "food_per_obstacle": 5
        }
    }
    
    # 1. Inisialisasi Game Logic
    W, H = config[LEVEL]["size"]
    OBSTACLES = config[LEVEL]["obstacles"]
    FOOD_PER_OBS = config[LEVEL]["food_per_obstacle"]
    game = SnakeGame(W, H, OBSTACLES, FOOD_PER_OBS)

    # 2. Inisialisasi Pygame
    pygame.init()
    SCREEN_WIDTH = W * BLOCK_SIZE + (W_PAD * 2)
    SCREEN_HEIGHT = H * BLOCK_SIZE + (H_PAD * 2)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(f"Snake Pathfinding - {ALGO} on {LEVEL} Level")
    clock = pygame.time.Clock()

    # Variabel untuk metrik (sama seperti sebelumnya)
    total_decision_time = 0
    total_nodes_expanded = 0
    decision_count = 0
    
    print(f"--- Menjalankan Level: {LEVEL} dengan Algoritma: {ALGO} ---")

    # 3. Eksekusi Simulasi (Game Loop Utama)
    running = True
    current_path_deque = deque()

    while running and not game.game_over:
        
        # 3a. Event Handling (Untuk menutup jendela)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # 3b. Algoritma mencari jalur (Logika BARU dengan Safe-Path Check)
        
        # Hanya cari jalur baru jika jalur saat ini habis
        if not current_path_deque:
            path_to_food = None
            nodes_expanded = 0
            
            # --- Mulai Logika Pathfinding ---
            start_time = time.perf_counter()
            
            # 1. Selalu coba cari jalur ke MAKANAN dulu
            if ALGO == "BFS":
                path_to_food, nodes = find_path_bfs(game, game.food)
            elif ALGO == "A*":
                path_to_food, nodes = find_path_a_star(game, game.food)
            
            nodes_expanded += nodes
            
            safe_path_found = False
            if path_to_food:
                # 2. Jika jalur ke makanan ADA, cek keamanannya
                if is_path_safe(game, path_to_food):
                    # 2a. AMAN! Gunakan jalur ini.
                    current_path_deque = deque(path_to_food[1:]) # [1:] karena [0] adalah kepala
                    safe_path_found = True
                else:
                    # 2b. DEAD-END TRAP! Abaikan makanan.
                    game.game_over_reason = "Dead-End Trap (Path Unsafe)" # Info
                    # (safe_path_found tetap False)
            
            # 3. Jika jalur ke makanan TIDAK AMAN atau TIDAK ADA
            if not safe_path_found:
                # Coba strategi bertahan: cari jalur ke EKOR
                path_to_tail = None
                if ALGO == "BFS":
                    path_to_tail, nodes = find_path_bfs(game, game.snake[-1]) # Goal: Ekor
                elif ALGO == "A*":
                    path_to_tail, nodes = find_path_a_star(game, game.snake[-1]) # Goal: Ekor
                
                nodes_expanded += nodes
                
                if path_to_tail:
                    current_path_deque = deque(path_to_tail[1:])
                else:
                    # 4. TERJEBAK! Tidak ada jalur ke makanan ATAU ekor
                    game.game_over = True
                    if not path_to_food:
                         game.game_over_reason = "No Path Found (Trapped)"
                    # (jika game_over_reason sudah di-set ke "Unsafe", biarkan saja)
            
            end_time = time.perf_counter()
            
            # Catat metrik HANYA saat kita membuat keputusan baru
            total_decision_time += (end_time - start_time)
            total_nodes_expanded += nodes_expanded
            decision_count += 1
            # --- Akhir Logika Pathfinding ---
        
        # 3c. Ular bergerak mengikuti path
        if current_path_deque:
            # Ambil langkah berikutnya dari jalur yang sudah disimpan
            next_step = current_path_deque.popleft()
            direction = get_direction_from_path(game.snake[0], next_step)
            game.move(direction)
            
            # Cek jika langkah ini diblokir oleh obstacle dinamis BARU
            # (Ini implementasi 'Replanning' poin 3 yang lebih sederhana)
            if game.game_over_reason == "Hit Dynamic Obstacle":
                current_path_deque.clear() # Hapus sisa jalur, paksa replan
                game.game_over = False # Batal game over, coba cari jalur lain
                game.game_over_reason = ""
                
        elif not game.game_over:
            # Ini seharusnya tidak terjadi jika logika di 3b benar
            game.game_over = True
            game.game_over_reason = "Pathfinding Logic Error"
            
        # 3d. Drawing (Menggambar ke layar)
        draw_game(screen, game, BLOCK_SIZE)
        
        # 3e. Update Display
        pygame.display.flip()
        
        # 3f. Kontrol Kecepatan Game
        clock.tick(GAME_SPEED_FPS) 

    # 4. Tampilkan Hasil (di Konsol)
    print("\n--- SIMULASI SELESAI ---")
    print(f"Algorithm: {ALGO}")
    print(f"Level: {LEVEL} ({W}x{H})")
    print(f"Total Food: {game.score}")
    print(f"Total Steps: {game.steps}")
    print(f"Game Over Reason: {game.game_over_reason}")
    print("\n--- Metrik Kinerja ---")
    print(f"Total Decisions: {decision_count}")
    
    if decision_count > 0:
        avg_time = (total_decision_time / decision_count) * 1000 # dalam ms
        avg_expansion = total_nodes_expanded / decision_count
        print(f"Average Time per Decision: {avg_time:.4f} ms")
        print(f"Average Nodes Expanded: {avg_expansion:.2f} nodes")

    # 5. Tampilkan Layar "Game Over" (di Pygame)
    if not running: # Jika ditutup manual
        pygame.quit()
    else:
        # Tampilkan pesan di tengah layar
        font = pygame.font.SysFont(None, 40)
        text_str = f"GAME OVER: {game.game_over_reason}"
        text = font.render(text_str, True, COLOR_WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        screen.blit(text, text_rect)
        pygame.display.flip()
        
        # Tunggu sampai pengguna menutup jendela
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            clock.tick(30)
        
        pygame.quit()
    
    # TODO: Tulis hasil ini ke file CSV sesuai proposal