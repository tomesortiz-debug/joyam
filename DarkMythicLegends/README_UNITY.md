# DARK MYTHIC LEGENDS — 20 Monster Low-Poly Pack

20 original rigged low-poly monsters, ~240–490 triangles each, with glowing
emissive accents (eyes, runes, weapons). Every rig shares the same skeleton and
contains **exactly the same three named animation clips**: `Idle` (2.0s loop),
`Walk` (1.0s loop) and `Attack` (0.9s).

Format: **animated GLB** (glTF 2.0 binary) — self-contained: mesh, skin,
materials and all 3 animation clips in one file. Scale is real-world meters
(monsters stand ~1.1 m to 2.2 m), Y-up, facing +Z.

## The roster

| Classic Gothic | Infernal | Frost & Storm | Ancients |
|---|---|---|---|
| Wraith King | Inferno Golem | Frost Revenant | Celestial Guardian |
| Bloodmoon Werewolf | Lava Imp | Storm Djinn | Obsidian Dragonling |
| Bone Colossus | Chaos Jester | Thunder Minotaur | Venom Naga |
| Spectral Knight | Abyss Demon | Crystal Basilisk | Iron Juggernaut |
| Plague Alchemist | Void Stalker | Sand Pharaoh | Shadow Assassin |

## Import into Unity

Unity does not read `.glb` natively — install Unity's official glTF importer
(one-time, 2 minutes):

1. **Window → Package Manager → + → Add package by name…**
2. Enter `com.unity.cloud.gltfast` and click **Add**
   (Unity 2020.3+; on older setups use the UnityGLTF package instead).
3. Drag the `GLB/` folder into your project's `Assets/`.
4. Each `.glb` imports as a prefab — drag it into the scene. Done.

The emissive parts glow on their own; add a **Bloom** post-processing effect
(URP/HDRP Volume → Bloom) to make them really pop.

## Playing the animations

Each imported asset contains three clips named `Idle`, `Walk`, `Attack`.

Set them up with an **Animator Controller**:

1. Right-click in Project → **Create → Animator Controller**.
2. Drag the `Idle`, `Walk`, `Attack` clips (found inside the imported .glb
   asset — expand its arrow) into the controller grid.
3. Add transitions (e.g. a `Speed` float for Idle↔Walk, an `Attack` trigger).
4. Add the controller to the prefab's **Animator** component.

Because *every* monster has identical clip names and skeleton layout, one
Animator Controller works for all 20 — build it once, reuse it everywhere.

```csharp
// Example driver
public class Monster : MonoBehaviour {
    Animator a;
    void Start()  => a = GetComponent<Animator>();
    void Update() {
        a.SetFloat("Speed", agentVelocity.magnitude);
        if (playerInRange) a.SetTrigger("Attack");
    }
}
```

## Regenerating / customizing

The whole pack is procedural — `tools/generate_pack.py` (pure Python, no
dependencies). Tweak palettes, sizes, horns, wings, weapons in the `ROSTER`
table and rerun to rebuild every GLB. `tools/render_preview.py` (needs
`numpy` + `pillow`) re-renders the contact sheet, optionally posed:
`python3 tools/render_preview.py Attack 0.55`.

## License

CC0 / public domain — generated content, use freely in commercial or
non-commercial games, no credit required.
