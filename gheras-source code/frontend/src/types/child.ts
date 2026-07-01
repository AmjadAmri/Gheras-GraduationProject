export interface Child {
  id: number;
  name: string;
  gender: "boy" | "girl";
  ageGroup: string;
  avatarUrl?: string;
  appearanceDescription?: string;
  photo?: string | null;
  storiesCount: number;
}
