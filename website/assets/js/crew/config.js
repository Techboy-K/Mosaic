/* Supabase connection for the crew portal.
   The anon key is designed to be public — it grants nothing on its own, because
   every table is behind Row Level Security. All authorization is decided in the
   database, never here. The service_role key must never appear in this file. */
window.MOSAIC_SUPABASE = {
  url: 'https://anekdtjxzkqwexeyzokc.supabase.co',
  anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFuZWtkdGp4emtxd2V4ZXl6b2tjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgyNDM5NTEsImV4cCI6MjEwMzgxOTk1MX0.89ea8ZOdeP1--FcNTINHTT4vvUSmURy81kuFF1sW1ng'
};
