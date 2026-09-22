class RoamingManager:
    def __init__(self):
        self.candidate = None
        self.since = 0.0
        self.last_switch = float("-inf")

    def reset(self):
        self.candidate = None

    def switched(self, now):
        self.last_switch = now
        self.reset()

    def should_switch(self, candidate_id, candidate_score, current_score, now, settings):
        if now - self.last_switch < settings.roaming_cooldown or candidate_score < current_score + settings.switch_threshold:
            self.reset()
            return False
        if self.candidate != candidate_id:
            self.candidate, self.since = candidate_id, now
            return False
        return now - self.since >= settings.sustain_seconds
