/* Public Supabase endpoint. The anon key grants nothing on its own: every table
   is behind Row Level Security, and the booking form can only reach one function,
   public_create_booking(), which inserts a pending booking and returns a reference. */
window.MOSAIC_PUBLIC = {
  url: 'https://anekdtjxzkqwexeyzokc.supabase.co',
  anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFuZWtkdGp4emtxd2V4ZXl6b2tjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgyNDM5NTEsImV4cCI6MjEwMzgxOTk1MX0.89ea8ZOdeP1--FcNTINHTT4vvUSmURy81kuFF1sW1ng',
  restaurants: {
    "Al Muroor": "24f97797-9d47-4af2-a189-bbc8169770df",
    "Al Najda": "0489816c-f545-47c5-aed7-7abf681bf234"
}
};
