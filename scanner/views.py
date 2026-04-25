import os
import joblib
import json
import numpy as np
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from .models import Profile, Feedback, ScanHistory
from ml.model import load_model, predict_url
from ml.feature_extractor import extract_features

# -------------------------------
# Authentication / Landing Views
# -------------------------------

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        age = request.POST.get('age')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            if age:
                try:
                    user.profile.age = int(age)
                    user.profile.save()
                except Exception:
                    pass
            messages.success(request, 'Account created. Please log in.')
            return redirect('login')
    return render(request, 'signup.html')


def logout_view(request):
    logout(request)
    return redirect('landing')

# -------------------------------
# User Dashboard / Profile / Feedback
# -------------------------------


    

@login_required
def dashboard(request):
    scans = ScanHistory.objects.filter(user=request.user).order_by("-created_at")[:20]
    return render(request, 'dashboard.html', {"scans": scans})


@login_required
def profile(request):
    if request.method == 'POST':
        age = request.POST.get('age')
        if age:
            request.user.profile.age = int(age)
            request.user.profile.save()
            messages.success(request, 'Profile updated.')
            return redirect('profile')
    return render(request, 'profile.html')


@login_required
def contact(request):
    return render(request, 'contact.html')


@login_required
def feedback(request):
    if request.method == 'POST':
        msg = request.POST.get('message')
        if msg:
            Feedback.objects.create(user=request.user, message=msg)
            messages.success(request, 'Thanks for your feedback!')
            return redirect('feedback')
    return render(request, 'feedback.html')


@login_required
def publish_feedback(request):
    data = Feedback.objects.all().order_by('-created_at')
    return render(request, 'publish_feedback.html', {'feedbacks': data})


# def history_view(request):
#     scans = ScanHistory.objects.all().order_by('-id')[:50]
#     return render(request, 'scanner/history.html', {'scans': scans})

def history_view(request):
    scans = ScanHistory.objects.all().order_by("-created_at")[:50]
    return render(request, 'scanner/history.html', {"scans": scans})

# -------------------------------
# ML Model & URL Scanner
# -------------------------------

MODEL_PATH = os.path.join(settings.BASE_DIR, "scanner", "ml", "model.pkl")

def _scan_url_local(url):
    clf = None
    if os.path.exists(MODEL_PATH):
        try:
            clf = joblib.load(MODEL_PATH)
        except:
            clf = None

    feats = {
        "length": len(url),
        "num_dots": url.count("."),
        "is_https": url.startswith("https"),
        "contains_kw": any(k in url.lower() for k in ["login", "secure", "account", "verify"])
    }

    if clf:
        try:
            arr = np.array([list(feats.values())], dtype=float)
            proba = clf.predict_proba(arr)[0]
            phish_prob = float(proba[1]) if clf.classes_[-1] == 1 else float(max(proba))
            return {
                "is_phishing": phish_prob > 0.5,
                "confidence": phish_prob,
                "features": feats,
                "explanations": ["ML-based decision"]
            }
        except:
            pass

    # fallback heuristics
    score = 0.0
    reasons = []
    if url.startswith("http://"):
        reasons.append("No HTTPS detected.")
        score += 0.3
    if feats["contains_kw"]:
        reasons.append("Suspicious keyword in URL.")
        score += 0.4
    if feats["num_dots"] >= 3:
        reasons.append("Too many subdomains.")
        score += 0.3

    return {
        "is_phishing": score > 0.5,
        "confidence": score,
        "features": feats,
        "explanations": reasons
    }

# -------------------------------
# Landing & Home
# -------------------------------

def landing(request):
    result, url, reasons = None, None, []
    if request.method == "POST":
        url = request.POST.get("url")
        if url:
            data = _scan_url_local(url)
            result = "Phishing" if data['is_phishing'] else "Safe"
            reasons = data.get("explanations", [])
    return render(request, "landing.html", {"result": result, "url": url, "reasons": reasons})


def home(request):
    result, url, reasons = None, None, []
    if request.method == "POST":
        url = request.POST.get("url")
        if url:
            data = _scan_url_local(url)
            result = "Phishing" if data['is_phishing'] else "Safe"
            reasons = data.get("explanations", [])
    return render(request, "home.html", {"result": result, "url": url, "reasons": reasons})



# -------------------------------
# API endpoints
# -------------------------------
@csrf_exempt
def api_scan(request):
    """
    Single endpoint:
    - If called via AJAX/JSON (home.html), return JsonResponse.
    - If called via normal POST/GET (landing), return scan_result.html.
    """
    if request.method == "POST":
        if request.content_type == "application/json":
            try:
                body = json.loads(request.body.decode("utf-8"))
                url = body.get("url", "").strip()
            except Exception:
                return JsonResponse({"error": "Invalid JSON."}, status=400)
        else:
            url = request.POST.get("url", "").strip()
    else:
        url = request.GET.get("url", "").strip()

    if not url:
        if request.content_type == "application/json":
            return JsonResponse({"error": "No URL provided."}, status=400)
        messages.error(request, "Please enter a URL to scan.")
        return redirect("home")

    try:
        clf = load_model()
        pred, proba, feats = predict_url(clf, url)
        is_phishing = bool(pred == 1)
        confidence = float(proba) * 100.0
    except Exception as e:
        if request.content_type == "application/json":
            return JsonResponse({"error": f"Prediction error: {e}"}, status=500)
        return render(request, "scanner/scan_result.html", {
            "url": url,
            "result": "Error",
            "confidence": 0.0,
            "is_phishing": False,
            "reasons": [f"Prediction error: {e}"],
            "features": {}
        })

    reasons = []
    if feats.get("is_https") is False:
        reasons.append("The URL does not use HTTPS.")
    if feats.get("contains_kw"):
        reasons.append("Suspicious keyword detected.")
    if feats.get("num_dots", 0) >= 3:
        reasons.append("Too many subdomains.")
    if not reasons:
        reasons.append("No strong red flags found.")

    result_text = "Phishing" if is_phishing else "Safe"

    # Save history if user logged in
    if request.user.is_authenticated:
        try:
            ScanHistory.objects.create(
                user=request.user if request.user.is_authenticated else None,
                url=url,
                result=result_text,
                probability=confidence,
                features=feats,
                reasons=reasons
                )
            print("✅ ScanHistory saved successfully")
        except IntegrityError as e:
            print("❌ IntegrityError:", e)
        except Exception as e:
            print("❌ Unexpected error while saving ScanHistory:", e)
        # try:
        #     ScanHistory.objects.create(
        #         user=request.user,
        #         url=url,
        #         result=result_text,
        #         probability=confidence,
        #         features=feats,
        #         # features=json.dumps(feats),
        #         # reasons=json.dumps(reasons),
        #         reasons=reasons,
        #         scanned_at=timezone.now()
        #     )
        # except Exception:
        #     pass
        
        

    # --- Return depending on request type ---
    if request.content_type == "application/json":
        return JsonResponse({
            "url": url,
            "result": result_text,
            "is_phishing": is_phishing,
            "confidence": confidence / 100.0,  # normalized 0-1 for frontend
            "features": feats,
            "reasons": reasons
        })

    return render(request, "scanner/scan_result.html", {
        "url": url,
        "result": result_text,
        "is_phishing": is_phishing,
        "confidence": confidence,
        "reasons": reasons,
        "features": feats
    })


def api_history(request):
    scans = ScanHistory.objects.order_by("-scanned_at")[:20]
    data = [
        {
            "url": s.url,
            "result": s.result,
            "probability": s.probability,
            "features": s.features,
            "reasons": s.reasons,
            "scanned_at": s.scanned_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for s in scans
    ]
    return JsonResponse({"history": data})

# @csrf_exempt
# def api_scan(request):
#     """
#     For full-page scan results (scan_result.html)
#     """
#     if request.method == "POST":
#         url = request.POST.get("url", "").strip()
#     else:
#         url = request.GET.get("url", "").strip()

#     if not url:
#         messages.error(request, "Please enter a URL to scan.")
#         return redirect("home")

#     try:
#         clf = load_model()
#         pred, proba, feats = predict_url(clf, url)
#         is_phishing = bool(pred == 1)
#         confidence = float(proba) * 100.0
#     except Exception as e:
#         return render(request, "scanner/scan_result.html", {
#             "url": url,
#             "result": "Error",
#             "confidence": 0.0,
#             "is_phishing": False,
#             "reasons": [f"Prediction error: {e}"],
#             "features": {}
#         })

#     reasons = []
#     if feats.get("is_https") is False:
#         reasons.append("The URL does not use HTTPS.")
#     if feats.get("contains_kw"):
#         reasons.append("Suspicious keyword detected.")
#     if feats.get("num_dots", 0) >= 3:
#         reasons.append("Too many subdomains.")
#     if not reasons:
#         reasons.append("No strong red flags found.")

#     result_text = "Phishing" if is_phishing else "Safe"

#     if request.user.is_authenticated:
#         try:
#             ScanHistory.objects.create(
#                 user=request.user,
#                 url=url,
#                 result=result_text,
#                 probability=confidence,
#                 features=json.dumps(feats),
#                 reasons=json.dumps(reasons),
#                 scanned_at=timezone.now()
#             )
#         except Exception:
#             pass

#     return render(request, "scanner/scan_result.html", {
#         "url": url,
#         "result": result_text,
#         "is_phishing": is_phishing,
#         "confidence": confidence,
#         "reasons": reasons,
#         "features": feats
#     })


# def api_history(request):
#     scans = ScanHistory.objects.order_by("-scanned_at")[:20]
#     data = [
#         {
#             "url": s.url,
#             "result": s.result,
#             "probability": s.probability,
#             "features": s.features,
#             "reasons": s.reasons,
#             "scanned_at": s.scanned_at.strftime("%Y-%m-%d %H:%M:%S"),
#         }
#         for s in scans
#     ]
#     return JsonResponse({"history": data})
# import os
# import joblib
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.models import User
# from .models import Profile, Feedback, ScanHistory   
# from .models import ScanHistory
# import json
# from django.http import JsonResponse
# from django.views.decorators.http import require_POST
# import numpy as np
# from ml.model import load_model, predict_url
# from ml.feature_extractor import extract_features
# from django.conf import settings
# from django.views.decorators.csrf import csrf_exempt

# def login_view(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         user = authenticate(request, username=username, password=password)
#         if user:
#             login(request, user)
#             return redirect('dashboard')
#         messages.error(request, 'Invalid username or password.')
#     return render(request, 'login.html')


# def signup_view(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         email = request.POST.get('email')
#         first_name = request.POST.get('first_name')
#         last_name = request.POST.get('last_name')
#         age = request.POST.get('age')
#         password = request.POST.get('password')

#         if User.objects.filter(username=username).exists():
#             messages.error(request, 'Username already taken.')
#         else:
#             user = User.objects.create_user(
#                 username=username,
#                 email=email,
#                 first_name=first_name,
#                 last_name=last_name,
#                 password=password
#             )
#             # Profile gets created by the signal; update age if provided
#             if age:
#                 try:
#                     user.profile.age = int(age)
#                     user.profile.save()
#                 except Exception:
#                     pass
#             messages.success(request, 'Account created. Please log in.')
#             return redirect('login')
#     return render(request, 'signup.html')


# def logout_view(request):
#     logout(request)
#     return redirect('landing')


# # -------------------------------
# # User Dashboard / Profile / Feedback
# # -------------------------------

# @login_required
# def dashboard(request):
#     return render(request, 'dashboard.html')


# @login_required
# def profile(request):
#     if request.method == 'POST':
#         age = request.POST.get('age')
#         if age:
#             request.user.profile.age = int(age)
#             request.user.profile.save()
#             messages.success(request, 'Profile updated.')
#             return redirect('profile')
#     return render(request, 'profile.html')


# @login_required
# def contact(request):
#     return render(request, 'contact.html')


# @login_required
# def feedback(request):
#     if request.method == 'POST':
#         msg = request.POST.get('message')
#         if msg:
#             Feedback.objects.create(user=request.user, message=msg)
#             messages.success(request, 'Thanks for your feedback!')
#             return redirect('feedback')
#     return render(request, 'feedback.html')


# @login_required
# def publish_feedback(request):
#     data = Feedback.objects.all().order_by('-created_at')
#     return render(request, 'publish_feedback.html', {'feedbacks': data})


# def history_view(request):
#     scans = ScanHistory.objects.all().order_by('-id')[:50]
#     return render(request, 'scanner/history.html', {'scans': scans})


# MODEL_PATH = os.path.join(settings.BASE_DIR, "scanner", "ml", "model.pkl")
# def home(request):
#     result = None
#     url = None
#     if request.method == "POST":
#         url = request.POST.get("url")
#         if url:
#             data = _scan_url_local(url)
#             result = "Phishing" if data['is_phishing'] else "Safe"
#     return render(request, "home.html", {"result": result, "url": url})

# # update landing same way
# def landing(request):
#     result = None
#     url = None
#     if request.method == "POST":
#         url = request.POST.get("url")
#         if url:
#             data = _scan_url_local(url)
#             result = "Phishing" if data['is_phishing'] else "Safe"
#     return render(request, "landing.html", {"result": result, "url": url})
# from django.utils import timezone

# from django.conf import settings
# from django.views.decorators.csrf import csrf_exempt

# # Load model once at import time
# try:
#     clf = load_model()
# except Exception as e:
#     clf = None
#     # optional: log the error or print
#     print("Model load error:", e)

# @csrf_exempt
# def api_scan(request):
#     """
#     Accepts POST (or GET with ?url=...) and returns rendered scan_result.html.
#     Shows: percentage confidence, Safe/Phishing, short explanations & features.
#     """
#     # accept GET or POST for quick tests
#     if request.method == "POST":
#         url = request.POST.get("url", "").strip()
#     else:
#         url = request.GET.get("url", "").strip()

#     if not url:
#         # Show home with a message or redirect to home
#         messages.error(request, "Please enter a URL to scan.")
#         return redirect("home")

#     # Ensure model loaded
#     global clf
#     if clf is None:
#         try:
#             clf = load_model()
#         except Exception as e:
#             # If model still not available, show friendly error
#             messages.error(request, "The detection model is not available. Please retrain it.")
#             return render(request, "scanner/scan_result.html", {
#                 "url": url,
#                 "result": "Error",
#                 "confidence": 0.0,
#                 "is_phishing": False,
#                 "reasons": ["Model not loaded. Run `python manage.py retrain_model` or check ml/model.pkl"],
#                 "features": {}
#             })

#     # Predict with helper (returns (pred, proba, feats))
#     try:
#         pred, proba, feats = predict_url(clf, url)
#         is_phishing = bool(pred == 1)
#         confidence = float(proba) * 100.0    # present as percentage
#     except Exception as e:
#         # handle unexpected errors in prediction gracefully
#         return render(request, "scanner/scan_result.html", {
#             "url": url,
#             "result": "Error",
#             "confidence": 0.0,
#             "is_phishing": False,
#             "reasons": [f"Prediction error: {e}"],
#             "features": {}
#         })

#     # Build small human-friendly reasons (3-4 lines) using feature flags
#     reasons = []
#     # The `feats` structure comes from feature_extractor; adjust keys if different
#     if feats.get("is_https") is False:
#         reasons.append("The URL does not use HTTPS (no TLS).")
#     if feats.get("contains_kw"):
#         reasons.append("Suspicious keyword(s) detected in the URL (like 'login'/'verify').")
#     if feats.get("bad_tld"):
#         reasons.append("Unusual top-level domain detected (may be suspicious).")
#     if feats.get("num_dots", 0) >= 3:
#         reasons.append("Many subdomains — could be hiding the real domain.")
#     if not reasons:
#         reasons.append("No strong red flags found — model confidence used to judge safety.")

#     result_text = "Phishing" if is_phishing else "Safe"

#     # If user is logged in, save history (your project already has a ScanHistory model)
#     try:
#         if request.user.is_authenticated:
#             ScanHistory.objects.create(user=request.user, url=url, is_phishing=is_phishing, confidence=confidence)
#     except Exception:
#         # ignore save errors for now (or log them)
#         pass

#     return render(request, "scanner/scan_result.html", {
#         "url": url,
#         "result": result_text,
#         "is_phishing": is_phishing,
#         "confidence": confidence,
#         "reasons": reasons,
#         "features": feats
#     })


# def api_history(request):
#     scans = ScanHistory.objects.order_by("-scanned_at")[:20]
#     data = [
#         {
#             "url": s.url,
#             "result": s.result,
#             "probability": s.probability,
#             "features": s.features,
#             "reasons": s.reasons,
#             "scanned_at": s.scanned_at.strftime("%Y-%m-%d %H:%M:%S"),
#         }
#         for s in scans
#     ]
#     return JsonResponse({"history": data})

# def _scan_url_local(url):
#     clf = None
#     if os.path.exists(MODEL_PATH):
#         try:
#             clf = joblib.load(MODEL_PATH)
#         except:
#             clf = None

#     feats = {"length": len(url), "dots": url.count("."), "has_https": url.startswith("https")}

#     if clf:
#         try:
#             arr = np.array([list(feats.values())], dtype=float)
#             proba = clf.predict_proba(arr)[0]
#             phish_prob = float(proba[1]) if clf.classes_[-1] == 1 else float(max(proba))
#             return {
#                 "is_phishing": phish_prob > 0.5,
#                 "confidence": phish_prob,
#                 "features": feats,
#                 "explanations": ["heuristic signals"],
#             }
#         except:
#             pass

#     # fallback
#     reasons = []
#     score = 0.0
#     if url.startswith("http://"):
#         reasons.append("No HTTPS")
#         score += 0.2
#     if any(k in url.lower() for k in ["login", "secure", "account", "verify"]):
#         reasons.append("Suspicious keyword")
#         score += 0.3

#     return {
#         "is_phishing": score > 0.4,
#         "confidence": score,
#         "features": feats,
#         "explanations": reasons,
#     }
