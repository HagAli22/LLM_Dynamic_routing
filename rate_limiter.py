"""
Advanced Rate Limiting and Protection System
============================================
Protects the system from abuse and overload with intelligent rate limiting.

Features:
- Token bucket algorithm for smooth rate limiting
- Per-user and per-IP rate limits
- Adaptive rate limiting based on system load
- DDoS protection
- Request throttling
- Quota management
"""

import time
import threading
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
from datetime import datetime


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10
    enable_adaptive: bool = True
    ban_threshold: int = 5  # Number of violations before temporary ban
    ban_duration: int = 3600  # Ban duration in seconds


@dataclass
class UserQuota:
    """User quota information"""
    user_id: str
    tier: str  # free, basic, premium, enterprise
    daily_limit: int
    used_today: int
    reset_time: float


class RateLimiter:
    """
    Advanced rate limiting system using token bucket algorithm
    
    Features:
    - Smooth rate limiting
    - Burst handling
    - Per-user limits
    - Adaptive throttling
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize rate limiter"""
        self.config = config or RateLimitConfig()
        
        # Token buckets for different time windows
        self.minute_buckets: Dict[str, deque] = defaultdict(deque)
        self.hour_buckets: Dict[str, deque] = defaultdict(deque)
        self.day_buckets: Dict[str, deque] = defaultdict(deque)
        
        # Violation tracking
        self.violations: Dict[str, int] = defaultdict(int)
        self.banned_until: Dict[str, float] = {}
        
        # User quotas
        self.user_quotas: Dict[str, UserQuota] = {}
        
        # System load tracking
        self.system_load: deque = deque(maxlen=100)
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        # Tier limits
        self.tier_limits = {
            "free": {"daily": 100, "hourly": 10, "minute": 5},
            "basic": {"daily": 1000, "hourly": 100, "minute": 20},
            "premium": {"daily": 10000, "hourly": 500, "minute": 50},
            "enterprise": {"daily": 100000, "hourly": 5000, "minute": 200}
        }
    
    
    def check_rate_limit(
        self,
        identifier: str,
        user_id: Optional[str] = None,
        tier: str = "free"
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if request is allowed under rate limits
        
        Args:
            identifier: IP address or session ID
            user_id: User identifier
            tier: User tier (free, basic, premium, enterprise)
        
        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        with self._lock:
            current_time = time.time()
            
            # Check if banned
            if identifier in self.banned_until:
                if current_time < self.banned_until[identifier]:
                    remaining = int(self.banned_until[identifier] - current_time)
                    return False, f"Temporarily banned. Try again in {remaining} seconds."
                else:
                    # Unban
                    del self.banned_until[identifier]
                    self.violations[identifier] = 0
            
            # Clean old entries
            self._cleanup_buckets(identifier, current_time)
            
            # Get tier limits
            limits = self.tier_limits.get(tier, self.tier_limits["free"])
            
            # Check minute limit
            minute_count = len(self.minute_buckets[identifier])
            if minute_count >= limits["minute"]:
                self._record_violation(identifier, current_time)
                return False, f"Rate limit exceeded: {limits['minute']} requests per minute"
            
            # Check hour limit
            hour_count = len(self.hour_buckets[identifier])
            if hour_count >= limits["hourly"]:
                self._record_violation(identifier, current_time)
                return False, f"Rate limit exceeded: {limits['hourly']} requests per hour"
            
            # Check day limit
            day_count = len(self.day_buckets[identifier])
            if day_count >= limits["daily"]:
                self._record_violation(identifier, current_time)
                return False, f"Daily quota exceeded: {limits['daily']} requests per day"
            
            # Check user quota if applicable
            if user_id:
                quota_ok, quota_msg = self._check_user_quota(user_id, tier)
                if not quota_ok:
                    return False, quota_msg
            
            # Check adaptive throttling
            if self.config.enable_adaptive:
                throttle_ok, throttle_msg = self._check_adaptive_throttle()
                if not throttle_ok:
                    return False, throttle_msg
            
            # All checks passed - record request
            self.minute_buckets[identifier].append(current_time)
            self.hour_buckets[identifier].append(current_time)
            self.day_buckets[identifier].append(current_time)
            
            if user_id and user_id in self.user_quotas:
                self.user_quotas[user_id].used_today += 1
            
            return True, None
    
    
    def _cleanup_buckets(self, identifier: str, current_time: float):
        """Remove old entries from buckets"""
        # Minute bucket (60 seconds)
        while (self.minute_buckets[identifier] and 
               current_time - self.minute_buckets[identifier][0] > 60):
            self.minute_buckets[identifier].popleft()
        
        # Hour bucket (3600 seconds)
        while (self.hour_buckets[identifier] and 
               current_time - self.hour_buckets[identifier][0] > 3600):
            self.hour_buckets[identifier].popleft()
        
        # Day bucket (86400 seconds)
        while (self.day_buckets[identifier] and 
               current_time - self.day_buckets[identifier][0] > 86400):
            self.day_buckets[identifier].popleft()
    
    
    def _record_violation(self, identifier: str, current_time: float):
        """Record a rate limit violation"""
        self.violations[identifier] += 1
        
        # Check if should ban
        if self.violations[identifier] >= self.config.ban_threshold:
            self.banned_until[identifier] = current_time + self.config.ban_duration
            print(f"⚠️ User/IP {identifier} temporarily banned for {self.config.ban_duration}s")
    
    
    def _check_user_quota(self, user_id: str, tier: str) -> Tuple[bool, Optional[str]]:
        """Check user-specific quota"""
        current_time = time.time()
        
        # Initialize quota if not exists
        if user_id not in self.user_quotas:
            daily_limit = self.tier_limits[tier]["daily"]
            self.user_quotas[user_id] = UserQuota(
                user_id=user_id,
                tier=tier,
                daily_limit=daily_limit,
                used_today=0,
                reset_time=self._get_next_reset_time()
            )
        
        quota = self.user_quotas[user_id]
        
        # Reset if needed
        if current_time >= quota.reset_time:
            quota.used_today = 0
            quota.reset_time = self._get_next_reset_time()
        
        # Check quota
        if quota.used_today >= quota.daily_limit:
            hours_until_reset = (quota.reset_time - current_time) / 3600
            return False, f"Daily quota exceeded. Resets in {hours_until_reset:.1f} hours."
        
        return True, None
    
    
    def _check_adaptive_throttle(self) -> Tuple[bool, Optional[str]]:
        """Adaptive throttling based on system load"""
        if not self.system_load:
            return True, None
        
        # Calculate average system load
        avg_load = sum(self.system_load) / len(self.system_load)
        
        # If system is overloaded (>80%), throttle requests
        if avg_load > 0.8:
            return False, "System is experiencing high load. Please retry in a moment."
        
        return True, None
    
    
    def record_system_load(self, load: float):
        """Record system load (0.0 to 1.0)"""
        with self._lock:
            self.system_load.append(load)
    
    
    def get_user_quota_info(self, user_id: str, tier: str = "free") -> Dict:
        """Get quota information for a user"""
        with self._lock:
            if user_id not in self.user_quotas:
                daily_limit = self.tier_limits[tier]["daily"]
                return {
                    "user_id": user_id,
                    "tier": tier,
                    "daily_limit": daily_limit,
                    "used_today": 0,
                    "remaining": daily_limit,
                    "reset_time": datetime.fromtimestamp(self._get_next_reset_time()).isoformat()
                }
            
            quota = self.user_quotas[user_id]
            return {
                "user_id": user_id,
                "tier": quota.tier,
                "daily_limit": quota.daily_limit,
                "used_today": quota.used_today,
                "remaining": quota.daily_limit - quota.used_today,
                "reset_time": datetime.fromtimestamp(quota.reset_time).isoformat()
            }
    
    
    def get_rate_limit_headers(self, identifier: str, tier: str = "free") -> Dict[str, str]:
        """Get rate limit headers (for API responses)"""
        with self._lock:
            limits = self.tier_limits[tier]
            
            return {
                "X-RateLimit-Limit-Minute": str(limits["minute"]),
                "X-RateLimit-Limit-Hour": str(limits["hourly"]),
                "X-RateLimit-Limit-Day": str(limits["daily"]),
                "X-RateLimit-Remaining-Minute": str(limits["minute"] - len(self.minute_buckets[identifier])),
                "X-RateLimit-Remaining-Hour": str(limits["hourly"] - len(self.hour_buckets[identifier])),
                "X-RateLimit-Remaining-Day": str(limits["daily"] - len(self.day_buckets[identifier])),
            }
    
    
    def reset_user(self, identifier: str):
        """Reset rate limits for a user (admin function)"""
        with self._lock:
            if identifier in self.minute_buckets:
                del self.minute_buckets[identifier]
            if identifier in self.hour_buckets:
                del self.hour_buckets[identifier]
            if identifier in self.day_buckets:
                del self.day_buckets[identifier]
            if identifier in self.violations:
                del self.violations[identifier]
            if identifier in self.banned_until:
                del self.banned_until[identifier]
    
    
    def unban_user(self, identifier: str):
        """Unban a user (admin function)"""
        with self._lock:
            if identifier in self.banned_until:
                del self.banned_until[identifier]
            if identifier in self.violations:
                self.violations[identifier] = 0
    
    
    def get_stats(self) -> Dict:
        """Get rate limiter statistics"""
        with self._lock:
            total_active_users = len(set(
                list(self.minute_buckets.keys()) +
                list(self.hour_buckets.keys()) +
                list(self.day_buckets.keys())
            ))
            
            return {
                "active_users": total_active_users,
                "banned_users": len(self.banned_until),
                "users_with_violations": len([v for v in self.violations.values() if v > 0]),
                "total_violations": sum(self.violations.values()),
                "avg_system_load": sum(self.system_load) / len(self.system_load) if self.system_load else 0.0
            }
    
    
    def _get_next_reset_time(self) -> float:
        """Get next daily reset time (midnight)"""
        now = datetime.now()
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if tomorrow <= now:
            tomorrow = tomorrow.replace(day=tomorrow.day + 1)
        return tomorrow.timestamp()


class DDoSProtection:
    """
    DDoS protection layer
    
    Detects and mitigates distributed denial of service attacks
    """
    
    def __init__(
        self,
        window_size: int = 60,
        threshold: int = 100,
        block_duration: int = 3600
    ):
        """
        Initialize DDoS protection
        
        Args:
            window_size: Time window in seconds for detection
            threshold: Request threshold to trigger protection
            block_duration: How long to block suspicious IPs
        """
        self.window_size = window_size
        self.threshold = threshold
        self.block_duration = block_duration
        
        self.request_log: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.blocked_ips: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    
    def check_request(self, ip_address: str) -> Tuple[bool, Optional[str]]:
        """
        Check if request should be allowed
        
        Returns:
            Tuple of (allowed, reason)
        """
        with self._lock:
            current_time = time.time()
            
            # Check if IP is blocked
            if ip_address in self.blocked_ips:
                if current_time < self.blocked_ips[ip_address]:
                    remaining = int(self.blocked_ips[ip_address] - current_time)
                    return False, f"IP blocked due to suspicious activity. Unblocked in {remaining}s"
                else:
                    del self.blocked_ips[ip_address]
            
            # Record request
            self.request_log[ip_address].append(current_time)
            
            # Clean old requests
            while (self.request_log[ip_address] and 
                   current_time - self.request_log[ip_address][0] > self.window_size):
                self.request_log[ip_address].popleft()
            
            # Check if threshold exceeded
            request_count = len(self.request_log[ip_address])
            if request_count > self.threshold:
                # Block IP
                self.blocked_ips[ip_address] = current_time + self.block_duration
                print(f"🚨 DDoS Protection: IP {ip_address} blocked ({request_count} requests in {self.window_size}s)")
                return False, "Too many requests. IP temporarily blocked."
            
            return True, None
    
    
    def unblock_ip(self, ip_address: str):
        """Unblock an IP address"""
        with self._lock:
            if ip_address in self.blocked_ips:
                del self.blocked_ips[ip_address]
    
    
    def get_stats(self) -> Dict:
        """Get protection statistics"""
        with self._lock:
            return {
                "blocked_ips": len(self.blocked_ips),
                "monitored_ips": len(self.request_log),
                "blocked_list": list(self.blocked_ips.keys())
            }
