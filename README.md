# 🎮 Noita-like Pixel Physics Game

Game 2D sandbox physics giống Noita được viết bằng Python với pygame.

## 📋 Tính năng

### Core Gameplay (Giống Noita)
- ✅ **Pixel-based world** - Mỗi pixel là một vật liệu với tính chất riêng
- ✅ **Falling sand simulation** - Cát rơi, nước chảy, lava lan
- ✅ **Terrain destructible** - Phá hủy từng pixel, tạo crater bằng explosion
- ✅ **Elemental reactions**:
  - Nước + Lava → Đá
  - Lửa + Gỗ → Tro
  - Acid ăn mòn terrain
- ✅ **Fire spread** - Lửa lan sang vật liệu cháy được

### Player System
- ✅ Di chuyển WASD
- ✅ Nhảy (Space)
- ✅ Bay bằng jetpack (Shift)
- ✅ HP system với UI
- ✅ Combat với wand/spell system

### Combat System
- ✅ Wand với nhiều spells
- ✅ Projectile physics
- ✅ Particle effects
- ✅ Camera shake khi nổ

### Enemy AI
- ✅ Slime enemies
- ✅ Pathfinding đơn giản
- ✅ Chase và attack player

### World Generation
- ✅ Procedural terrain với noise
- ✅ Chunk system cho optimization
- ✅ Multiple biomes (surface, underground, lava pools)

### Render & Optimization
- ✅ Batch rendering với numpy
- ✅ Camera follow player
- ✅ Camera shake effect
- ✅ Chỉ update vùng gần player
- ✅ FPS counter

## 🚀 Cài đặt

### Yêu cầu
- Python 3.8+
- pygame
- numpy
- noise (optional - cho procedural generation tốt hơn)

### Cài đặt dependencies
```bash
pip install pygame numpy noise
```

## 🎮 Cách chơi

### Controls
| Phím | Chức năng |
|------|-----------|
| W/A/S/D hoặc Mũi tên | Di chuyển |
| Space | Nhảy |
| Shift | Jetpack (bay) |
| Mouse Left | Shoot spell / Place material |
| Mouse Right | Explosion / Clear area |
| 1-5 | Đổi spell/material |
| +/- | Tăng/giảm brush size |
| R | Respawn |
| P | Pause |
| ESC | Thoát |

### Spells
1. **Spark** - Mana thấp, bắn nhanh
2. **Fireball** - Sát thương cao, tạo lửa
3. **Water Bolt** - Bắn nước, dập lửa
4. **Lava** (brush) - Đặt lava
5. **Stone** (brush) - Đặt đá

### Materials Available
- `AIR` (0) - Không khí
- `SAND` (1) - Cát rơi
- `WATER` (2) - Nước chảy
- `LAVA` (3) - Nham thạch, nóng chảy
- `STONE` (4) - Đá cứng
- `WOOD` (5) - Gỗ, cháy được
- `FIRE` (6) - Lửa, lan rộng
- `SMOKE` (7) - Khói, bay lên
- `ASH` (8) - Tro
- `ACID` (9) - Acid, ăn mòn
- `ICE` (10) - Băng

## 🏗️ Cấu trúc Project

```
/game
├── main.py              # Entry point, game loop
├── settings.py          # Cấu hình game
├── engine/
│   ├── physics.py       # Pixel physics engine
│   ├── renderer.py      # Render system với camera
│   └── world.py         # World management với chunks
├── entities/
│   ├── player.py        # Player entity
│   └── enemy.py         # Enemy AI
├── systems/
│   ├── sand_simulation.py  # Optimized falling sand
│   └── combat.py           # Combat & spells
└── assets/
    ├── tiles/
    └── sprites/
```

## 🔧 Kiến trúc

### ECS/Component-based
- **Entities**: Player, Enemy có components (position, velocity, sprite)
- **Systems**: Physics, Render, Combat xử lý logic
- **Components**: Data-only classes

### Optimization Techniques
1. **Chunk System**: Chia world thành chunks 64x64
2. **Active Region Update**: Chỉ update pixels gần player
3. **NumPy Arrays**: Xử lý grid nhanh hơn list
4. **Batch Rendering**: Render theo material type
5. **Direction Alternating**: Tránh bias trong falling sand

## 💡 Ví dụ Demo

### Chạy game:
```bash
python main.py
```

### Test physics riêng:
```python
from systems.sand_simulation import SandSimulation

sim = SandSimulation()
sim.fill_circle(100, 50, 10, SAND)  # Tạo đống cát
sim.update()  # Update physics
```

## 🎯 Các hiệu ứng đặc biệt

### Reactions
```python
# Water + Lava = Stone
# Fire + Wood = Ash + Smoke
# Acid + Stone = Sand
```

### Particle System
- Explosion particles
- Smoke rising
- Fire spreading

### Camera Effects
- Smooth follow player
- Shake on explosion
- Bounds checking

## 📈 Performance Tips

1. Giảm `update_radius` trong `simulation.update()` nếu lag
2. Giảm `WORLD_WIDTH` và `WORLD_HEIGHT` trong settings
3. Tăng `TILE_SIZE` để render ít pixels hơn
4. Tắt noise library nếu không cần procedural generation phức tạp

## 🔮 Future Enhancements

- [ ] Multi-threading cho simulation
- [ ] GPU acceleration với moderngl
- [ ] Thêm nhiều spells và wands
- [ ] Boss enemies
- [ ] Save/Load world
- [ ] Multiplayer
- [ ] Sound effects
- [ ] More biomes và structures

## 📝 License

Free to use for learning and experimentation!

---

**Enjoy destroying everything! 💥**