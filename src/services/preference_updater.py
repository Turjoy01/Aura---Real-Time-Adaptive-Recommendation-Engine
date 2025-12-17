from src.models.preference import UserPreferenceProfile, CategoryScore, PriceRange, LocationPreference
from src.db.mongodb import get_collection
from datetime import datetime
from typing import Optional

class PreferenceUpdater:
    """Real-time preference profile updater using reinforcement learning"""
    
    @staticmethod
    async def update_from_behavior(
        user_id: str,
        behavior_type: str,
        event_data: dict = None,
        reward: Optional[float] = None
    ) -> None:
        """
        Update user preference profile based on behavior event
        Implements real-time learning without batch jobs
        """
        collection = await get_collection("user_preference_profile")
        
        # Get or create user profile
        profile = await collection.find_one({"user_id": user_id})
        
        if not profile:
            profile = {
                "user_id": user_id,
                "updated_at": datetime.utcnow(),
                "preferred_categories": [],
                "preferred_locations": [],
                "total_events_attended": 0,
                "cold_start_completed": False
            }
        
        # Update based on behavior type and reward
        if reward is not None:
            await PreferenceUpdater._apply_reward(profile, behavior_type, reward, event_data)
        
        profile["updated_at"] = datetime.utcnow()
        
        # Upsert profile
        await collection.update_one(
            {"user_id": user_id},
            {"$set": profile},
            upsert=True
        )
        
        # Invalidate cache (simplified - in production use Redis)
        # cache.invalidate(f"user_profile:{user_id}")

    @staticmethod
    async def _apply_reward(
        profile: dict,
        behavior_type: str,
        reward: float,
        event_data: dict = None
    ) -> None:
        """Apply reward to update preferences"""
        
        if behavior_type == "purchase" or behavior_type == "attend":
            # Strong signal: +1.0 for purchase/attendance
            if event_data:
                category = event_data.get("category", "Unknown")
                price = event_data.get("price", 0)
                location = event_data.get("location", {})
                
                # Update category preference
                existing = next(
                    (c for c in profile.get("preferred_categories", []) if c["name"] == category),
                    None
                )
                
                if existing:
                    existing["score"] = min(1.0, existing["score"] + reward * 0.15)
                else:
                    profile.setdefault("preferred_categories", []).append({
                        "name": category,
                        "score": max(0, reward * 0.5)
                    })
                
                # Update price range
                if not profile.get("preferred_price_range"):
                    profile["preferred_price_range"] = {
                        "avg": price,
                        "max_ever_paid": price,
                        "sweet_spot_min": price * 0.8,
                        "sweet_spot_max": price * 1.2
                    }
                else:
                    pr = profile["preferred_price_range"]
                    pr["avg"] = (pr.get("avg", 0) + price) / 2
                    pr["max_ever_paid"] = max(pr.get("max_ever_paid", 0), price)
                
                # Update location preference
                if location:
                    city = location.get("city")
                    neighborhood = location.get("neighborhood")
                    
                    if city:
                        existing_loc = next(
                            (l for l in profile.get("preferred_locations", []) 
                             if l["city"] == city and l.get("neighborhood") == neighborhood),
                            None
                        )
                        
                        if existing_loc:
                            existing_loc["score"] = min(1.0, existing_loc["score"] + reward * 0.1)
                        else:
                            profile.setdefault("preferred_locations", []).append({
                                "city": city,
                                "neighborhood": neighborhood,
                                "score": max(0, reward * 0.4)
                            })
                
                # Increment attendance counter
                profile["total_events_attended"] = profile.get("total_events_attended", 0) + 1
                
                # Mark cold start as completed after 3 events
                if profile.get("total_events_attended", 0) >= 3:
                    profile["cold_start_completed"] = True
        
        elif behavior_type == "skip":
            # Negative signal for skips - reduce scores
            if event_data:
                category = event_data.get("category")
                if category:
                    existing = next(
                        (c for c in profile.get("preferred_categories", []) if c["name"] == category),
                        None
                    )
                    if existing:
                        existing["score"] = max(0, existing["score"] - 0.05)

    @staticmethod
    async def get_profile(user_id: str) -> Optional[dict]:
        """Get user preference profile"""
        collection = await get_collection("user_preference_profile")
        return await collection.find_one({"user_id": user_id})
