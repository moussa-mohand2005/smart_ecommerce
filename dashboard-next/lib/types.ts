export type Product = {
  product_id: number;
  product_name: string;
  brand: string;
  product_url: string | null;
  image_url_main: string | null;
  current_price: number;
  currency: string;
  rating_avg: number;
  reviews_count: number;
  stock_status: string;
  material: string | null;
  sole_type: string | null;
  closure: string | null;
  gender: string | null;
  persona_json: string | null;
  ml_score: number;
  predicted_success: number;
  cluster_id: number;
  pca_x: number | null;
  pca_y: number | null;
};

export type Persona = {
  productId: number;
  productName: string;
  brand: string;
  name: string;
  age: string;
  lifestyle: string;
  traits: string;
  occasion: string;
};

export type DashboardData = {
  generatedAt: string;
  filters: { brands: string[]; priceMax: number };
  kpis: { total: number; avgScore: number; brands: number; luxury: number; medianPrice: number; inStock: number };
  topPicks: Product[];
  marketScatter: Array<{ name: string; brand: string; price: number; score: number; reviews: number; cluster: number }>;
  priceBands: Array<{ band: string; count: number; avgScore: number }>;
  clusters: Array<{ cluster: string; count: number; avgScore: number }>;
  styleMap: Array<{ name: string; x: number; y: number; cluster: number; score: number }>;
  personas: Persona[];
  brandStats: Array<{ brand: string; products: number; avgScore: number; avgPrice: number; reviews: number }>;
  correlations: Array<{ antecedents: string; consequents: string; lift: number }>;
  products: Product[];
  pagination: { page: number; pageSize: number; total: number; pages: number };
};
