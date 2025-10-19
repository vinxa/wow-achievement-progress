const TTL_MS = 15 * 60 * 1000; // 15min cache

async function loadAchievements(region, realm, character) {
    const key = `achv_${region}_${realm}_${character}`.toLowerCase();
    const cached = localStorage.getItem(key);
    if (cached) {
        const { timestamp, data } = JSON.parse(cached);
        if (Date.now() - timestamp < TTL_MS) {
            return data;
        }
    }
    const resp = await fetch(`/achievements?region=${region}&realm=${realm}&character=${character}`);
    const data = await resp.json();
    localStorage.setItem(key, JSON.stringify({ timestamp: Date.now(), data }));
    return data;
}

function findAchievement(data, id) {
    function searchCriteria(criteria) {
        for (const c of criteria || []) {
            if (c.id === id) return c;
            const found = searchCriteria(c.children);
            if (found) return found;
        }
        return null;
    }
    for (const ach of data.achievements || []) {
        if (ach.id === id) return ach;
        const found = searchCriteria(ach.criteria);
        if (found) return found;
    }
    return null;
}

async function getAchievementProgress(region, realm, character, achId) {
    const fullData = await loadAchievements(region, realm, character);
    return findAchievement(fullData, Number(achId));
}
