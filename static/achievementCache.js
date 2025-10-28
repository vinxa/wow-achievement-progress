const TTL_MS = 15 * 60 * 1000; // 15min cache

async function loadCharacterAchievements(region, realm, character) {
    const key = `achv_${region}_${realm}_${character}`.toLowerCase();
    const cached = localStorage.getItem(key);
    if (cached) {
        const { timestamp, data } = JSON.parse(cached);
        if (Date.now() - timestamp < TTL_MS) {
            console.log(`Been ${((Date.now() - timestamp)/1000/60).toPrecision(2)}min since last update. Loading achievements from cache.`);
            return data;
        }
    }
    const resp = await fetch(`/achievement?region=${region}&server=${realm}&character=${character}`);
    const data = await resp.json();
    if (!("error:" in data)) localStorage.setItem(key, JSON.stringify({ timestamp: Date.now(), data }));
    return data;
}

function findAchievement(data, id) {
    function searchCriteria(criteria) {
        for (const c of criteria || []) {
            if (c.id === id) return c;
            const found = searchCriteria(c.children || c.criteria);
            if (found) return found;
        }
        return null;
    }
    for (const ach of data || []) {
        if (ach.id === id) return ach;
        const found = searchCriteria(ach.criteria || ach.children);
        if (found) return found;
    }
    return null;
}

async function getAchievementProgress(region, realm, character, achId) {
    const fullData = await loadCharacterAchievements(region, realm, character);
    if ("error" in fullData) return {"error": "Error: Character not found! Please check your inputs."};
    return findAchievement(fullData, Number(achId));
}