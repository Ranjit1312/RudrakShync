# Placeholder for supabase client connection setup
from supabase import create_client
import os

SUPABASE_URL = "https://rysoibmhqswfoswqnbgn.supabase.co" #os.getenv("SUPABASE_URL")
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ5c29pYm1ocXN3Zm9zd3FuYmduIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMxOTk0OTUsImV4cCI6MjA1ODc3NTQ5NX0.Br0-uD80NU5r_i1BaZ1YJSQ41ZvgTSZvT9hSHQFtB2Y"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
