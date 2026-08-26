class AIFeatureExtractor:
    @staticmethod
    def extract_linear_features(points):
        if not points:
            return {"curbs": [], "crests": [], "rails": []}
        curbs = [(p[0], p[1], p[2]) for p in points if abs(p[0] - 25.0) < 4.0]
        crests = [(p[0], p[1], p[2]) for p in points if p[2] > 20.0]
        rails = [(p[0], p[1], p[2]) for p in points if abs(p[1]) < 3.0]
        return {"curbs": curbs, "crests": crests, "rails": rails}
