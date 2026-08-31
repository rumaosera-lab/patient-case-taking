"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  registerPatient,
  createSession,
  submitClinicalHistory,
  generateCaseSummary,
  updateSessionStatus,
  uploadPatientDocument,
  getPatientTimeline,
  CaseSummaryData,
  ClinicalHistoryUpdatePayload,
  TimelineEventItem,
} from "@/services/patientApi";

type Language = "English" | "Hindi" | "Marathi";

interface SpeechRecognitionResultLike {
  [index: number]: { transcript: string };
}

interface SpeechRecognitionEventLike {
  results?: {
    [index: number]: SpeechRecognitionResultLike;
  };
  error?: string;
}

interface SpeechRecognitionInstance {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onstart: (() => void) | null;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: SpeechRecognitionEventLike) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance;

export interface PatientCaseData {
  problemArea: string | null;
  chiefIssue: string;
  duration: string;
  onset: string;
  severity: number;
  pattern: string;
  triggers: string[];
  triggerNotes: string;
  conditions: string[];
  hasPastSurgeries: boolean | null;
  surgeryDetails: string;
  takesMedications: boolean | null;
  medicationDetails: string;
  allergies: string[];
  familyConditions: string[];
  diet: string;
  smoking: string;
  alcohol: string;
  sleep: string;
  systemicSymptoms: string[];
  reportStatus: string;
}

const initialCaseData: PatientCaseData = {
  problemArea: null,
  chiefIssue: "",
  duration: "",
  onset: "",
  severity: 5,
  pattern: "",
  triggers: [],
  triggerNotes: "",
  conditions: [],
  hasPastSurgeries: null,
  surgeryDetails: "",
  takesMedications: null,
  medicationDetails: "",
  allergies: [],
  familyConditions: [],
  diet: "",
  smoking: "",
  alcohol: "",
  sleep: "",
  systemicSymptoms: [],
  reportStatus: "",
};

const content = {
  English: {
    greeting: "Namaste 🙏",
    chooseLanguage: "Please choose your preferred language",
    englishSub: "Proceed in English",
    hindiSub: "हिंदी में आगे बढ़ें",
    marathiSub: "मराठीत पुढे जा",

    abhaLabel: "ENTER 14-DIGIT ABHA ID",
    abhaPlaceholder: "00-0000-0000-0000",
    passcode: "••••",
    testing: "Testing phase: use passcode 1234",
    login: "Login",
    loggingIn: "Connecting...",
    invalidPasscode: "Invalid passcode. Please use 1234 for testing.",

    ayush: "🌿 AYUSH mode OFF",
    ayushOn: "🌿 AYUSH mode ON",
    doctor: "🩺 Doctor login",
    timeline: "📈 My health timeline",

    // Step 1
    step: "STEP 1 OF 14",
    problemTitle: "📍 Where is the problem?",
    problemSubtitle: "Please select the area where you are experiencing a problem",
    head: "🧠 Head",
    eyes: "👁️ Eyes",
    mouth: "🦷 Teeth / Mouth",
    chest: "🫁 Chest / Breathing",
    stomach: "🤢 Stomach",
    bones: "🦴 Bones / Joints",
    hands: "✋ Hands",
    legs: "🦵 Legs",
    other: "➕ Other / Not sure",

    // Step 2
    step2: "STEP 2 OF 14",
    issueTitle: "What problem are you experiencing?",
    issueSubtitle: "You can speak naturally or type your problem below",
    selectedAreaLabel: "Selected area:",
    speak: "🎤 Start speaking",
    listening: "🎤 Listening...",
    typePlaceholder: "For example: I have had sharp stomach pain after meals for 2 days...",
    or: "OR",

    // Step 3
    step3: "STEP 3 OF 14",
    durationTitle: "How long have you had this issue?",
    durationSubtitle: "Select the duration and how the problem began",
    dur_24h: "Under 24 Hours",
    dur_24h_sub: "Started recently today",
    dur_3d: "1 to 3 Days",
    dur_3d_sub: "Started a few days ago",
    dur_2w: "1 to 2 Weeks",
    dur_2w_sub: "Ongoing for a week or two",
    dur_1m: "1 to 3 Months",
    dur_1m_sub: "Persistent for several weeks",
    dur_6m: "Over 6 Months",
    dur_6m_sub: "Long term / Chronic issue",
    onsetLabel: "HOW DID IT START?",
    onsetSudden: "⚡ Sudden",
    onsetGradual: "📈 Gradual",

    // Step 4
    step4: "STEP 4 OF 14",
    severityTitle: "How severe is your discomfort?",
    severitySubtitle: "Rate the intensity on a scale from 1 (Mild) to 10 (Very Severe)",
    mild: "Mild (1-3)",
    moderate: "Moderate (4-6)",
    severe: "Severe (7-10)",
    patternLabel: "DISCOMFORT PATTERN",
    pat_constant: "Constant (Always there)",
    pat_intermittent: "Comes and goes",
    pat_worsening: "Getting worse over time",
    pat_improving: "Gradually improving",

    // Step 5
    step5: "STEP 5 OF 14",
    triggersTitle: "What makes it worse or better?",
    triggersSubtitle: "Select all factors that affect your condition",
    trig_movement: "🏃 Physical movement / Walking",
    trig_food: "🍽️ Food / Eating meals",
    trig_rest: "🛏️ Rest / Lying down",
    trig_stress: "⚡ Stress / Anxiety",
    trig_night: "🌙 Night time / Cold air",
    trig_none: "🛡️ Nothing specific",

    // Step 6
    step6: "STEP 6 OF 14",
    conditionsTitle: "Do you have existing diagnosed conditions?",
    conditionsSubtitle: "Select any medical conditions you are currently diagnosed with",
    cond_diabetes: "🩺 Diabetes",
    cond_bp: "💓 High Blood Pressure (Hypertension)",
    cond_thyroid: "🦋 Thyroid Disorder",
    cond_asthma: "🫁 Asthma / Chronic Lung Disease",
    cond_heart: "❤️ Heart Disease",
    cond_kidney: "🫘 Kidney Disease",
    cond_none: "🛡️ None of these",

    // Step 7
    step7: "STEP 7 OF 14",
    surgeryTitle: "Any past surgeries or major hospitalizations?",
    surgerySubtitle: "Let us know if you have undergone any medical operations",
    yes: "Yes",
    no: "No",
    surgeryPlaceholder: "Please describe past surgeries and approximate year...",

    // Step 8
    step8: "STEP 8 OF 14",
    medsTitle: "Are you taking regular medications?",
    medsSubtitle: "Include daily prescriptions, AYUSH remedies, or supplements",
    medsPlaceholder: "List your current medications (e.g. Metformin 500mg, Telmisartan 40mg)...",

    // Step 9
    step9: "STEP 9 OF 14",
    allergiesTitle: "Do you have any known allergies?",
    allergiesSubtitle: "Select any known drug, food, or environmental allergies",
    all_penicillin: "💊 Penicillin / Antibiotics",
    all_painkillers: "💉 Painkillers / NSAIDs (Aspirin, Ibuprofen)",
    all_dust: "🌾 Dust / Pollen / Inhalants",
    all_food: "🥜 Food Allergies (Nuts, Dairy, Gluten)",
    all_none: "🛡️ No Known Allergies",

    // Step 10
    step10: "STEP 10 OF 14",
    familyTitle: "Family Medical History",
    familySubtitle: "Have your parents or siblings had any major health conditions?",
    fam_diabetes: "🩺 Diabetes",
    fam_bp: "💓 High Blood Pressure",
    fam_heart: "❤️ Heart Attack / Heart Disease",
    fam_cancer: "🎗️ Cancer",
    fam_stroke: "🧠 Stroke / Paralysis",
    fam_none: "🛡️ None / Not aware",

    // Step 11
    step11: "STEP 11 OF 14",
    lifestyleTitle: "Personal & Lifestyle Habits",
    lifestyleSubtitle: "Select your daily habits to help the doctor tailor care",
    dietLabel: "DIET PREFERENCE",
    diet_veg: "🥗 Vegetarian",
    diet_nonveg: "🍗 Non-Vegetarian",
    diet_egg: "🥚 Eggetarian",
    smokingLabel: "TOBACCO / SMOKING",
    smoke_never: "Never",
    smoke_former: "Former",
    smoke_active: "Current Active",
    alcoholLabel: "ALCOHOL CONSUMPTION",
    alc_never: "Never",
    alc_occasional: "Occasional",
    alc_regular: "Regular",
    sleepLabel: "SLEEP QUALITY",
    sleep_good: "Good (7-8 hrs)",
    sleep_disturbed: "Disturbed",
    sleep_poor: "Poor (< 5 hrs)",

    // Step 12
    step12: "STEP 12 OF 14",
    rosTitle: "Review of Other Symptoms",
    rosSubtitle: "Are you experiencing any of these systemic symptoms?",
    ros_fever: "🌡️ Fever or Chills",
    ros_fatigue: "⚡ Severe Fatigue / Weakness",
    ros_weight: "⚖️ Unexplained Weight Loss",
    ros_dizziness: "💫 Dizziness / Fainting",
    ros_cough: "😮‍💨 Cough or Breathlessness",
    ros_nausea: "🤢 Nausea or Vomiting",
    ros_none: "🛡️ No other symptoms",

    // Step 13
    step13: "STEP 13 OF 14",
    reportsTitle: "Prior Medical Records & Reports",
    reportsSubtitle: "Select how previous lab reports or prescriptions will be shared",
    rep_abha: "📱 Linked via ABHA / ABDM Locker",
    rep_abha_sub: "Digital records fetched automatically",
    rep_physical: "📄 Physical copies with patient",
    rep_physical_sub: "Carrying printed reports today",
    rep_portal: "📸 Uploaded on Patient Portal",
    rep_portal_sub: "Available on clinic record system",
    rep_none: "🚫 No previous medical records",
    rep_none_sub: "First time consultation",
    uploadTitle: "Upload Medical Documents",
    uploadSubtitle: "Upload prescription, lab report, or discharge summary (PDF, JPG, PNG)",
    uploadButton: "Choose Document / File to Upload",
    uploading: "Uploading & processing document...",
    uploadedTitle: "Uploaded Documents",

    // Step 14
    step14: "STEP 14 OF 14",
    summaryTitle: "Clinical Case Intake Summary",
    summarySubtitle: "Review your completed medical questionnaire before sending to the doctor",
    submitCase: "Submit Clinical Intake →",
    submittingCase: "Submitting to Doctor...",

    // Confirmation Screen
    successTitle: "Case Intake Submitted Successfully!",
    successSubtitle: "Your clinical history has been formatted into FHIR standards and sent directly to the doctor's queue.",
    tokenLabel: "OPD QUEUE TOKEN",
    doctorAssigned: "Assigned: General Medicine · Chamber 04",
    startNew: "Start New Patient Intake",

    back: "← Back",
    next: "Next →",
  },

  Hindi: {
    greeting: "नमस्ते 🙏",
    chooseLanguage: "कृपया अपनी भाषा चुनें",
    englishSub: "अंग्रेज़ी में आगे बढ़ें",
    hindiSub: "हिंदी में आगे बढ़ें",
    marathiSub: "मराठी में आगे बढ़ें",

    abhaLabel: "14 अंकों की ABHA ID दर्ज करें",
    abhaPlaceholder: "00-0000-0000-0000",
    passcode: "पासकोड",
    testing: "परीक्षण चरण: पासकोड 1234 का उपयोग करें",
    login: "लॉगिन",
    loggingIn: "कनेक्ट हो रहा है...",
    invalidPasscode: "अमान्य पासकोड। परीक्षण के लिए 1234 का उपयोग करें।",

    ayush: "🌿 आयुष मोड बंद",
    ayushOn: "🌿 आयुष मोड चालू",
    doctor: "🩺 डॉक्टर लॉगिन",
    timeline: "📈 मेरी स्वास्थ्य जानकारी",

    // Step 1
    step: "14 में से चरण 1",
    problemTitle: "📍 समस्या कहाँ है?",
    problemSubtitle: "कृपया उस जगह का चयन करें जहाँ आपको समस्या हो रही है",
    head: "🧠 सिर",
    eyes: "👁️ आँखें",
    mouth: "🦷 दाँत / मुँह",
    chest: "🫁 छाती / साँस लेने में समस्या",
    stomach: "🤢 पेट",
    bones: "🦴 हड्डियाँ / जोड़",
    hands: "✋ हाथ",
    legs: "🦵 पैर",
    other: "➕ अन्य / पता नहीं",

    // Step 2
    step2: "14 में से चरण 2",
    issueTitle: "आपको क्या समस्या हो रही है?",
    issueSubtitle: "आप बोलकर बता सकते हैं या नीचे लिख सकते हैं",
    selectedAreaLabel: "चयनित क्षेत्र:",
    speak: "🎤 बोलना शुरू करें",
    listening: "🎤 सुन रहा हूँ...",
    typePlaceholder: "उदाहरण: मुझे 2 दिनों से खाने के बाद पेट में तेज दर्द हो रहा है...",
    or: "या",

    // Step 3
    step3: "14 में से चरण 3",
    durationTitle: "यह समस्या कितने समय से है?",
    durationSubtitle: "समस्या की अवधि और शुरुआत का चयन करें",
    dur_24h: "24 घंटे से कम",
    dur_24h_sub: "आज ही शुरू हुआ",
    dur_3d: "1 से 3 दिन",
    dur_3d_sub: "कुछ दिनों पहले शुरू हुआ",
    dur_2w: "1 से 2 सप्ताह",
    dur_2w_sub: "एक-दो हफ्ते से जारी है",
    dur_1m: "1 से 3 महीने",
    dur_1m_sub: "कई हफ्तों से लगातार",
    dur_6m: "6 महीने से अधिक",
    dur_6m_sub: "पुरानी / लंबी समस्या",
    onsetLabel: "शुरुआत कैसे हुई?",
    onsetSudden: "⚡ अचानक",
    onsetGradual: "📈 धीरे-धीरे",

    // Step 4
    step4: "14 में से चरण 4",
    severityTitle: "तकलीफ या दर्द कितना गंभीर है?",
    severitySubtitle: "1 (हल्का) से 10 (अत्यधिक गंभीर) के पैमाने पर चुनें",
    mild: "हल्का (1-3)",
    moderate: "मध्यम (4-6)",
    severe: "गंभीर (7-10)",
    patternLabel: "दर्द का प्रकार",
    pat_constant: "लगातार (हमेशा बना रहता है)",
    pat_intermittent: "आता-जाता रहता है",
    pat_worsening: "समय के साथ बढ़ रहा है",
    pat_improving: "धीरे-धीरे सुधर रहा है",

    // Step 5
    step5: "14 में से चरण 5",
    triggersTitle: "किन चीज़ों से समस्या बढ़ती या घटती है?",
    triggersSubtitle: "लागू होने वाले सभी कारक चुनें",
    trig_movement: "🏃 चलने-फिरने / शारीरिक हलचल से",
    trig_food: "🍽️ खाना खाने के बाद",
    trig_rest: "🛏️ आराम करने / लेटने पर",
    trig_stress: "⚡ तनाव / चिंता से",
    trig_night: "🌙 रात में / ठंड में",
    trig_none: "🛡️ कुछ खास नहीं",

    // Step 6
    step6: "14 में से चरण 6",
    conditionsTitle: "क्या आपको पहले से कोई बीमारी है?",
    conditionsSubtitle: "निदान की गई पुरानी बीमारियों का चयन करें",
    cond_diabetes: "🩺 मधुमेह (Diabetes)",
    cond_bp: "💓 उच्च रक्तचाप (High BP)",
    cond_thyroid: "🦋 थायराइड",
    cond_asthma: "🫁 अस्थमा / दमा",
    cond_heart: "❤️ हृदय रोग",
    cond_kidney: "🫘 गुर्दे की बीमारी",
    cond_none: "🛡️ इनमें से कोई नहीं",

    // Step 7
    step7: "14 में से चरण 7",
    surgeryTitle: "क्या कोई पिछली सर्जरी या अस्पताल में भर्ती हुई है?",
    surgerySubtitle: "यदि आपका कोई ऑपरेशन हुआ है तो बताएं",
    yes: "हाँ",
    no: "नहीं",
    surgeryPlaceholder: "सर्जरी का विवरण और अनुमानित वर्ष लिखें...",

    // Step 8
    step8: "14 में से चरण 8",
    medsTitle: "क्या आप कोई नियमित दवाई ले रहे हैं?",
    medsSubtitle: "नियमित दवाएं, आयुष या सप्लीमेंट्स शामिल करें",
    medsPlaceholder: "वर्तमान दवाओं के नाम लिखें...",

    // Step 9
    step9: "14 में से चरण 9",
    allergiesTitle: "क्या आपको कोई ज्ञात एलर्जी है?",
    allergiesSubtitle: "दवा या खाद्य पदार्थों की एलर्जी चुनें",
    all_penicillin: "💊 पेनिसिलिन / एंटीबायोटिक्स",
    all_painkillers: "💉 दर्द निवारक दवाइयाँ (NSAIDs)",
    all_dust: "🌾 धूल / परागकण",
    all_food: "🥜 खाद्य एलर्जी (दूध, मेवे)",
    all_none: "🛡️ कोई ज्ञात एलर्जी नहीं",

    // Step 10
    step10: "14 में से चरण 10",
    familyTitle: "पारिवारिक चिकित्सा इतिहास",
    familySubtitle: "क्या परिवार में किसी को कोई गंभीर स्वास्थ्य समस्या रही है?",
    fam_diabetes: "🩺 मधुमेह",
    fam_bp: "💓 उच्च रक्तचाप",
    fam_heart: "❤️ दिल का दौरा / हृदय रोग",
    fam_cancer: "🎗️ कैंसर",
    fam_stroke: "🧠 स्ट्रोक / पक्षाघात",
    fam_none: "🛡️ कोई नहीं / जानकारी नहीं",

    // Step 11
    step11: "14 में से चरण 11",
    lifestyleTitle: "जीवनशैली और दैनिक आदतें",
    lifestyleSubtitle: "अपनी आदतों का चयन करें",
    dietLabel: "आहार प्रकार",
    diet_veg: "🥗 शाकाहारी",
    diet_nonveg: "🍗 मांसाहारी",
    diet_egg: "🥚 अंडा युक्त शाकाहारी",
    smokingLabel: "तंबाकू / धूम्रपान",
    smoke_never: "कभी नहीं",
    smoke_former: "पहले पीते थे",
    smoke_active: "वर्तमान में सक्रिय",
    alcoholLabel: "शराब / मद्यपान",
    alc_never: "कभी नहीं",
    alc_occasional: "कभी-कभार",
    alc_regular: "नियमित",
    sleepLabel: "नींद की गुणवत्ता",
    sleep_good: "अच्छी (7-8 घंटे)",
    sleep_disturbed: "टूटी-फूटी",
    sleep_poor: "खराब (< 5 घंटे)",

    // Step 12
    step12: "14 में से चरण 12",
    rosTitle: "अन्य शारीरिक लक्षण",
    rosSubtitle: "क्या आपको इनमें से कोई अन्य लक्षण हैं?",
    ros_fever: "🌡️ बुखार या ठंड लगना",
    ros_fatigue: "⚡ अत्यधिक थकान / कमजोरी",
    ros_weight: "⚖️ अचानक वजन कम होना",
    ros_dizziness: "💫 चक्कर आना",
    ros_cough: "😮‍💨 खांसी या सांस फूलना",
    ros_nausea: "🤢 उल्टी या जी मिचलाना",
    ros_none: "🛡️ अन्य कोई लक्षण नहीं",

    // Step 13
    step13: "14 में से चरण 13",
    reportsTitle: "पुरानी मेडिकल रिपोर्ट और पर्चियां",
    reportsSubtitle: "पुरानी रिपोर्ट कैसे उपलब्ध हैं, चुनें",
    rep_abha: "📱 आभा / ABDM लॉकर से जुड़ा है",
    rep_abha_sub: "डिजिटल रिकॉर्ड सीधे प्राप्त होंगे",
    rep_physical: "📄 कागजी रिपोर्ट साथ में हैं",
    rep_physical_sub: "आज प्रिंट रिपोर्ट साथ लाए हैं",
    rep_portal: "📸 पोर्टल पर पहले से अपलोड है",
    rep_portal_sub: "सिस्टम में उपलब्ध है",
    rep_none: "🚫 कोई पूर्व रिपोर्ट नहीं",
    rep_none_sub: "पहली बार परामर्श",
    uploadTitle: "मेडिकल दस्तावेज अपलोड करें",
    uploadSubtitle: "पर्ची, लैब रिपोर्ट या डिस्चार्ज समरी अपलोड करें (PDF, JPG, PNG)",
    uploadButton: "अपलोड करने के लिए फाइल चुनें",
    uploading: "दस्तावेज अपलोड हो रहा है...",
    uploadedTitle: "अपलोड किए गए दस्तावेज",

    // Step 14
    step14: "14 में से चरण 14",
    summaryTitle: "केस इनटेक सारांश",
    summarySubtitle: "डॉक्टर को भेजने से पहले अपनी जानकारी की समीक्षा करें",
    submitCase: "केस इनटेक जमा करें →",
    submittingCase: "डॉक्टर को भेजा जा रहा है...",

    // Confirmation Screen
    successTitle: "केस इनटेक सफलतापूर्वक जमा हो गया!",
    successSubtitle: "आपकी चिकित्सा जानकारी डॉक्टर के पास भेज दी गई है।",
    tokenLabel: "ओपीडी कतार टोकन",
    doctorAssigned: "निर्धारित: जनरल मेडिसिन · कक्ष 04",
    startNew: "नया मरीज इनटेक शुरू करें",

    back: "← वापस",
    next: "आगे बढ़ें →",
  },

  Marathi: {
    greeting: "नमस्कार 🙏",
    chooseLanguage: "कृपया तुमची भाषा निवडा",
    englishSub: "इंग्रजीमध्ये पुढे जा",
    hindiSub: "हिंदीमध्ये पुढे जा",
    marathiSub: "मराठीत पुढे जा",

    abhaLabel: "14 अंकी ABHA ID प्रविष्ट करा",
    abhaPlaceholder: "00-0000-0000-0000",
    passcode: "पासकोड",
    testing: "चाचणी टप्पा: पासकोड 1234 वापरा",
    login: "लॉगिन",
    loggingIn: "कनेक्ट करत आहे...",
    invalidPasscode: "अवैध पासकोड. चाचणीसाठी 1234 वापरा.",

    ayush: "🌿 आयुष मोड बंद",
    ayushOn: "🌿 आयुष मोड चालू",
    doctor: "🩺 डॉक्टर लॉगिन",
    timeline: "📈 माझी आरोग्य माहिती",

    // Step 1
    step: "14 पैकी टप्पा 1",
    problemTitle: "📍 समस्या कुठे आहे?",
    problemSubtitle: "कृपया तुम्हाला ज्या भागात समस्या आहे तो भाग निवडा",
    head: "🧠 डोके",
    eyes: "👁️ डोळे",
    mouth: "🦷 दात / तोंड",
    chest: "🫁 छाती / श्वास घेणे",
    stomach: "🤢 पोट",
    bones: "🦴 हाडे / सांधे",
    hands: "✋ हात",
    legs: "🦵 पाय",
    other: "➕ इतर / माहिती नाही",

    // Step 2
    step2: "14 पैकी टप्पा 2",
    issueTitle: "तुम्हाला काय समस्या होत आहे?",
    issueSubtitle: "तुम्ही बोलू शकता किंवा खाली लिहू शकता",
    selectedAreaLabel: "निवडलेला भाग:",
    speak: "🎤 बोलायला सुरुवात करा",
    listening: "🎤 ऐकत आहे...",
    typePlaceholder: "उदाहरण: मला २ दिवसांपासून जेवणानंतर पोटात तीव्र वेदना होत आहेत...",
    or: "किंवा",

    // Step 3
    step3: "14 पैकी टप्पा 3",
    durationTitle: "हा त्रास किती दिवसांपासून आहे?",
    durationSubtitle: "त्रासाचा कालावधी आणि सुरुवात कशी झाली ते निवडा",
    dur_24h: "२४ तासांपेक्षा कमी",
    dur_24h_sub: "आजच सुरू झाले",
    dur_3d: "१ ते ३ दिवस",
    dur_3d_sub: "काही दिवसांपूर्वी सुरू झाले",
    dur_2w: "१ ते २ आठवडे",
    dur_2w_sub: "गेल्या १-२ आठवड्यांपासून",
    dur_1m: "१ ते ३ महिने",
    dur_1m_sub: "काही महिन्यांपासून सतत",
    dur_6m: "६ महिन्यांपेक्षा जास्त",
    dur_6m_sub: "दीर्घकालीन जुना आजार",
    onsetLabel: "सुरुवात कशी झाली?",
    onsetSudden: "⚡ अचानक",
    onsetGradual: "📈 हळूहळू",

    // Step 4
    step4: "14 पैकी टप्पा 4",
    severityTitle: "त्रास किंवा वेदना किती तीव्र आहेत?",
    severitySubtitle: "१ (कमी) ते १० (अत्यंत तीव्र) श्रेणीतून निवडा",
    mild: "कमी (1-3)",
    moderate: "मध्यम (4-6)",
    severe: "तीव्र (7-10)",
    patternLabel: "वेदनेचे स्वरूप",
    pat_constant: "सतत (नेहमी त्रास होतो)",
    pat_intermittent: "येतो-जातो",
    pat_worsening: "काळानुसार वाढत आहे",
    pat_improving: "हळूहळू कमी होत आहे",

    // Step 5
    step5: "14 पैकी टप्पा 5",
    triggersTitle: "कशाने हा त्रास वाढतो किंवा कमी होतो?",
    triggersSubtitle: "लागू होणारे सर्व घटक निवडा",
    trig_movement: "🏃 हालचाल / चालण्याने",
    trig_food: "🍽️ जेवणानंतर / खाल्ल्यावर",
    trig_rest: "🛏️ विश्रांती घेतल्यावर",
    trig_stress: "⚡ ताणतणाव / थकवा",
    trig_night: "🌙 रात्रीच्या वेळी / थंडीत",
    trig_none: "🛡️ काही विशिष्ट नाही",

    // Step 6
    step6: "14 पैकी टप्पा 6",
    conditionsTitle: "तुम्हाला आधीपासून काही आजार आहेत का?",
    conditionsSubtitle: "निदान झालेले जुने आजार निवडा",
    cond_diabetes: "🩺 मधुमेह (Diabetes)",
    cond_bp: "💓 उच्च रक्तदाब (High BP)",
    cond_thyroid: "🦋 थायरॉईड",
    cond_asthma: "🫁 दमा / अस्थमा",
    cond_heart: "❤️ हृदयविकार",
    cond_kidney: "🫘 मूत्रपिंडाचे आजार",
    cond_none: "🛡️ यांपैकी काहीही नाही",

    // Step 7
    step7: "14 पैकी टप्पा 7",
    surgeryTitle: "यापूर्वी शस्त्रक्रिया किंवा रुग्णालयात दाखल व्हावे लागले होते का?",
    surgerySubtitle: "शस्त्रक्रिया झाली असल्यास माहिती द्या",
    yes: "होय",
    no: "नाही",
    surgeryPlaceholder: "शस्त्रक्रियेचा तपशील आणि वर्ष लिहा...",

    // Step 8
    step8: "14 पैकी टप्पा 8",
    medsTitle: "तुम्ही सध्या कोणती नियमित औषधे घेत आहात का?",
    medsSubtitle: "नियमित औषधे, आयुष किंवा सप्लिमेंट्स समाविष्ट करा",
    medsPlaceholder: "सध्या सुरू असणाऱ्या औषधांची नावे लिहा...",

    // Step 9
    step9: "14 पैकी टप्पा 9",
    allergiesTitle: "तुम्हाला कोणत्याही प्रकारची ॲलर्जी आहे का?",
    allergiesSubtitle: "औषध किंवा अन्नाची ॲलर्जी असल्यास निवडा",
    all_penicillin: "💊 पेनिसिलिन / प्रतिजैविके (Antibiotics)",
    all_painkillers: "💉 वेदनाशामक औषधे (NSAIDs)",
    all_dust: "🌾 धूळ / परागकण",
    all_food: "🥜 अन्न ॲलर्जी (दूध, शेंगदाणे)",
    all_none: "🛡️ कोणतीही ॲलर्जी नाही",

    // Step 10
    step10: "14 पैकी टप्पा 10",
    familyTitle: "कौटुंबिक आरोग्य इतिहास",
    familySubtitle: "कुटुंबात कोणाला काही गंभीर आजार आहे का?",
    fam_diabetes: "🩺 मधुमेह",
    fam_bp: "💓 उच्च रक्तदाब",
    fam_heart: "❤️ हृदयविकाराचा झटका",
    fam_cancer: "🎗️ कर्करोग",
    fam_stroke: "🧠 पक्षाघात / स्ट्रोक",
    fam_none: "🛡️ काही नाही / माहिती नाही",

    // Step 11
    step11: "14 पैकी टप्पा 11",
    lifestyleTitle: "जीवनशैली आणि सवयी",
    lifestyleSubtitle: "तुमच्या दैनंदिन सवयींची माहिती निवडा",
    dietLabel: "आहाराचा प्रकार",
    diet_veg: "🥗 शाकाहारी",
    diet_nonveg: "🍗 मांसाहारी",
    diet_egg: "🥚 अंड्यांचा समावेश असलेले शाकाहारी",
    smokingLabel: "तंबाखू / धुम्रपान",
    smoke_never: "कधीच नाही",
    smoke_former: "पूर्वी करत होतो",
    smoke_active: "सध्या सुरू आहे",
    alcoholLabel: "मद्यपान",
    alc_never: "कधीच नाही",
    alc_occasional: "कधीतरी",
    alc_regular: "नियमित",
    sleepLabel: "झोपेचा दर्जा",
    sleep_good: "चांगली (७-८ तास)",
    sleep_disturbed: "अशांत",
    sleep_poor: "कमी (< ५ तास)",

    // Step 12
    step12: "14 पैकी टप्पा 12",
    rosTitle: "इतर शारीरिक लक्षणे",
    rosSubtitle: "तुम्हाला खालीलपैकी इतर काही लक्षणे जाणवत आहेत का?",
    ros_fever: "🌡️ ताप किंवा थंडी वाजणे",
    ros_fatigue: "⚡ तीव्र थकवा / अशक्तपणा",
    ros_weight: "⚖️ अचानक वजन कमी होणे",
    ros_dizziness: "💫 चक्कर येणे",
    ros_cough: "😮‍💨 खोकला किंवा दम लागणे",
    ros_nausea: "🤢 मळमळ किंवा उलटी",
    ros_none: "🛡️ इतर कोणतीही लक्षणे नाहीत",

    // Step 13
    step13: "14 पैकी टप्पा 13",
    reportsTitle: "मागील तपासणी अहवाल आणि कागदपत्रे",
    reportsSubtitle: "मागील अहवाल कसे उपलब्ध आहेत ते निवडा",
    rep_abha: "📱 आभा लॉकरद्वारे जोडलेले आहे",
    rep_abha_sub: "डिजिटल अहवाल थेट प्राप्त होतील",
    rep_physical: "📄 कागदी अहवाल सोबत आहेत",
    rep_physical_sub: "आज अहवाल सोबत आणले आहेत",
    rep_portal: "📸 पोर्टलवर अपलोड केले आहेत",
    rep_portal_sub: "सिस्टीममध्ये उपलब्ध",
    rep_none: "🚫 कोणतेही मागील अहवाल नाहीत",
    rep_none_sub: "पहिलीच तपासणी",
    uploadTitle: "वैद्यकीय कागदपत्रे अपलोड करा",
    uploadSubtitle: "प्रिस्क्रिप्शन, लॅब रिपोर्ट किंवा डिस्चार्ज समरी अपलोड करा (PDF, JPG, PNG)",
    uploadButton: "अपलोड करण्यासाठी फाइल निवडा",
    uploading: "कागदपत्र अपलोड होत आहे...",
    uploadedTitle: "अपलोड केलेली कागदपत्रे",

    // Step 14
    step14: "14 पैकी टप्पा 14",
    summaryTitle: "वैद्यकीय केस सारांश",
    summarySubtitle: "डॉक्टरांकडे पाठवण्यापूर्वी तुमच्या माहितीची पडताळणी करा",
    submitCase: "केस इनटेक जमा करा →",
    submittingCase: "डॉक्टरांकडे पाठवले जात आहे...",

    // Confirmation Screen
    successTitle: "केस इनटेक यशस्वीरीत्या जमा झाले!",
    successSubtitle: "तुमचा वैद्यकीय इतिहास डॉक्टरांच्या संगणकावर पाठवला गेला आहे.",
    tokenLabel: "ओपीडी टोकन क्रमांक",
    doctorAssigned: "डॉक्टर: जनरल मेडिसिन · कक्ष ०४",
    startNew: "नवीन रुग्ण तपासणी सुरू करा",

    back: "← मागे",
    next: "पुढे जा →",
  },
};

const voiceText = {
  English:
    "Namaste. Please choose your preferred language. Enter your 14 digit ABHA ID and passcode to continue.",
  Hindi:
    "नमस्ते। कृपया अपनी पसंदीदा भाषा चुनें। आगे बढ़ने के लिए अपनी 14 अंकों की आभा आईडी और पासकोड दर्ज करें।",
};

const problemAreaSpeech: Record<Language, Record<string, string>> = {
  English: {
    head: "Head",
    eyes: "Eyes",
    mouth: "Teeth and Mouth",
    chest: "Chest and Breathing",
    stomach: "Stomach",
    bones: "Bones and Joints",
    hands: "Hands",
    legs: "Legs",
    other: "Other or Not sure",
  },
  Hindi: {
    head: "सिर",
    eyes: "आँखें",
    mouth: "दाँत और मुँह",
    chest: "छाती और साँस लेने में समस्या",
    stomach: "पेट",
    bones: "हड्डियाँ और जोड़",
    hands: "हाथ",
    legs: "पैर",
    other: "अन्य या पता नहीं",
  },
  Marathi: {
    head: "डोके",
    eyes: "डोळे",
    mouth: "दात आणि तोंड",
    chest: "छाती आणि श्वास घेणे",
    stomach: "पोट",
    bones: "हाडे आणि सांधे",
    hands: "हात",
    legs: "पाय",
    other: "इतर किंवा माहिती नाही",
  },
};

const clinicalSections = [
  { key: "complaint", label: "COMPLAINT" },
  { key: "history", label: "HISTORY" },
  { key: "past", label: "PAST" },
  { key: "drugs", label: "DRUGS" },
  { key: "family", label: "FAMILY" },
  { key: "personal", label: "PERSONAL" },
  { key: "ros", label: "ROS" },
  { key: "reports", label: "REPORTS" },
];

function getActiveSectionKey(step: number): string {
  if (step <= 2) return "complaint";
  if (step <= 5) return "history";
  if (step <= 7) return "past";
  if (step <= 9) return "drugs";
  if (step === 10) return "family";
  if (step === 11) return "personal";
  if (step === 12) return "ros";
  return "reports";
}

function KioskTopBar() {
  return (
    <header className="kiosk-top-bar">
      <div className="brand-left">
        <div className="brand-icon-box">✚</div>
        <div className="brand-title-group">
          <span className="brand-name">MediKiosk</span>
          <span className="brand-sub">Clinical Intake System</span>
        </div>
      </div>
      <div className="brand-right">
        <div className="status-pill">
          <span className="status-dot"></span>
          <span>SYSTEM ONLINE</span>
        </div>
        <span className="station-tag">STATION-04 · OPD</span>
      </div>
    </header>
  );
}

function ClinicalStepper({ currentStep }: { currentStep: number }) {
  const activeKey = getActiveSectionKey(currentStep);

  return (
    <nav aria-label="Clinical Questionnaire Progress" className="clinical-stepper-wrap">
      <div className="clinical-stepper">
        {clinicalSections.map((sec, idx) => {
          const isActive = sec.key === activeKey;
          return (
            <div
              key={sec.key}
              style={{ display: "flex", alignItems: "center", gap: "6px" }}
            >
              <div className={`step-item ${isActive ? "active" : ""}`}>
                <span>{sec.label}</span>
              </div>
              {idx < clinicalSections.length - 1 && (
                <span className="step-chevron">›</span>
              )}
            </div>
          );
        })}
      </div>
    </nav>
  );
}

function KioskFooter() {
  return (
    <footer className="kiosk-footer">
      <div className="footer-left">
        <span className="footer-dot"></span>
        <span>ABHA / ABDM Connected</span>
        <span>·</span>
        <span>FHIR v4.0.1</span>
      </div>
      <div className="footer-center">
        <span>MediKiosk Clinical Intake System v2.4</span>
      </div>
      <div className="footer-right">
        <span>Decision-support draft · Physician approval required</span>
      </div>
    </footer>
  );
}

export default function Home() {
  const router = useRouter();

  const [selectedLanguage, setSelectedLanguage] =
    useState<Language>("English");

  const [loggedIn, setLoggedIn] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const [patientId, setPatientId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isSubmittingLogin, setIsSubmittingLogin] = useState(false);
  const [isSubmittingCase, setIsSubmittingCase] = useState(false);
  const [summaryData, setSummaryData] = useState<CaseSummaryData | null>(null);

  const [abhaId, setAbhaId] = useState("11111111111111");
  const [passcode, setPasscode] = useState("1234");
  const [loginError, setLoginError] = useState("");

  const [caseData, setCaseData] = useState<PatientCaseData>(initialCaseData);
  const [isListening, setIsListening] = useState(false);

  const [ayushActive, setAyushActive] = useState(false);
  const [voicesLoaded, setVoicesLoaded] = useState(false);

  // Document upload state (used in Step 13)
  const [uploadedFiles, setUploadedFiles] = useState<{ name: string; docId: string }[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Timeline modal state
  const [showTimeline, setShowTimeline] = useState(false);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEventItem[]>([]);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [timelineError, setTimelineError] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);

  const t = content[selectedLanguage];

  const updateCase = <K extends keyof PatientCaseData>(
    field: K,
    value: PatientCaseData[K]
  ) => {
    setCaseData((prev) => ({ ...prev, [field]: value }));
  };

  const toggleArrayItem = (field: "triggers" | "conditions" | "allergies" | "familyConditions" | "systemicSymptoms", item: string) => {
    setCaseData((prev) => {
      const list = prev[field];
      if (list.includes(item)) {
        return { ...prev, [field]: list.filter((x) => x !== item) };
      } else {
        return { ...prev, [field]: [...list, item] };
      }
    });
  };

  useEffect(() => {
    const loadVoices = () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        const voices = window.speechSynthesis.getVoices();
        if (voices.length > 0) {
          setVoicesLoaded(true);
        }
      }
    };

    loadVoices();

    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }

    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.onvoiceschanged = null;
        window.speechSynthesis.cancel();
      }

      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
        audioRef.current = null;
      }

      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {
          // Ignore
        }
        recognitionRef.current = null;
      }
    };
  }, []);

  const speak = (language: Language) => {
    if (typeof window === "undefined") return;

    if (language === "Marathi") {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }

      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }

      const audio = new Audio("/audio/marathi.mp3");
      audioRef.current = audio;

      audio.play().catch((err) => {
        console.error("Failed to play Marathi audio:", err);
      });
      return;
    }

    if (!("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel();

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }

    let textToSpeak = voiceText[language as "English" | "Hindi"];
    if (!textToSpeak) return;

    const voices = window.speechSynthesis.getVoices();
    let selectedVoice: SpeechSynthesisVoice | undefined;
    let selectedLang = "en-IN";

    if (language === "English") {
      selectedVoice = voices.find((v) =>
        v.lang.toLowerCase().startsWith("en")
      );
      selectedLang = "en-IN";
    } else if (language === "Hindi") {
      const hindiVoice = voices.find((v) =>
        v.lang.toLowerCase().startsWith("hi")
      );
      if (hindiVoice) {
        selectedVoice = hindiVoice;
        selectedLang = "hi-IN";
      } else {
        selectedVoice = voices.find((v) =>
          v.lang.toLowerCase().startsWith("en")
        );
        selectedLang = "en-IN";
        textToSpeak =
          "Namaste. Kripya apni pasandida bhasha chunein. Aage badhne ke liye apni 14 anko ki ABHA ID aur passcode darj karein.";
      }
    }

    const speech = new SpeechSynthesisUtterance(textToSpeak);
    if (selectedVoice) {
      speech.voice = selectedVoice;
    }
    speech.lang = selectedLang;
    speech.rate = 0.85;
    speech.pitch = 1;
    speech.volume = 1;

    window.speechSynthesis.speak(speech);
  };

  const speakProblemArea = (key: string, language: Language) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }

    const textToSpeak = problemAreaSpeech[language]?.[key];
    if (!textToSpeak) return;

    const speech = new SpeechSynthesisUtterance(textToSpeak);
    const voices = window.speechSynthesis.getVoices();

    if (language === "English") {
      const englishVoice = voices.find((v) =>
        v.lang.toLowerCase().startsWith("en")
      );
      if (englishVoice) {
        speech.voice = englishVoice;
      }
      speech.lang = "en-IN";
    } else if (language === "Hindi") {
      const hindiVoice = voices.find((v) =>
        v.lang.toLowerCase().startsWith("hi")
      );
      if (hindiVoice) {
        speech.voice = hindiVoice;
      }
      speech.lang = "hi-IN";
    } else if (language === "Marathi") {
      const marathiVoice = voices.find((v) =>
        v.lang.toLowerCase().startsWith("mr")
      );
      if (marathiVoice) {
        speech.voice = marathiVoice;
      }
      speech.lang = "mr-IN";
    }

    speech.rate = 0.85;
    speech.pitch = 1;
    speech.volume = 1;

    window.speechSynthesis.speak(speech);
  };

  const toggleListening = (onTranscript: (t: string) => void) => {
    if (typeof window === "undefined") return;

    if (isListening) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {
          // Ignore
        }
        recognitionRef.current = null;
      }
      setIsListening(false);
      return;
    }

    const SpeechRecognitionClass =
      (
        window as unknown as {
          SpeechRecognition?: SpeechRecognitionConstructor;
          webkitSpeechRecognition?: SpeechRecognitionConstructor;
        }
      ).SpeechRecognition ||
      (
        window as unknown as {
          SpeechRecognition?: SpeechRecognitionConstructor;
          webkitSpeechRecognition?: SpeechRecognitionConstructor;
        }
      ).webkitSpeechRecognition;

    if (!SpeechRecognitionClass) {
      return;
    }

    try {
      const recognition = new SpeechRecognitionClass();
      recognition.continuous = false;
      recognition.interimResults = false;

      if (selectedLanguage === "English") {
        recognition.lang = "en-IN";
      } else if (selectedLanguage === "Hindi") {
        recognition.lang = "hi-IN";
      } else if (selectedLanguage === "Marathi") {
        recognition.lang = "mr-IN";
      }

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: SpeechRecognitionEventLike) => {
        const transcript = event.results?.[0]?.[0]?.transcript;
        if (transcript) {
          onTranscript(transcript);
        }
      };

      recognition.onerror = (event: SpeechRecognitionEventLike) => {
        console.error("Speech recognition error:", event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
        recognitionRef.current = null;
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error("Failed to start speech recognition:", err);
      setIsListening(false);
    }
  };

  const handleProblemAreaSelect = (key: string) => {
    updateCase("problemArea", key);
    speakProblemArea(key, selectedLanguage);
  };

  const handleLanguageSelect = (language: Language) => {
    setSelectedLanguage(language);
    setLoginError("");

    /* Marathi MP3 plays directly */
    if (language === "Marathi") {
      speak(language);
      return;
    }

    /* English + Hindi Speech Synthesis */
    if (voicesLoaded || typeof window !== "undefined") {
      speak(language);
    }
  };

  const handleLogin = async () => {
    if (passcode.trim() !== "1234") {
      setLoginError(t.invalidPasscode);
      return;
    }
    setLoginError("");
    setIsSubmittingLogin(true);

    const langCodeMap: Record<Language, "en" | "hi" | "mr"> = {
      English: "en",
      Hindi: "hi",
      Marathi: "mr",
    };
    const preferredLang = langCodeMap[selectedLanguage] || "en";

    try {
      // Step 1: Register or retrieve patient record from FastAPI backend
      const digitsOnly = abhaId.replace(/\D/g, "");
      const cleanPhone = `98${digitsOnly.slice(0, 8).padEnd(8, "0")}`;

      const regRes = await registerPatient({
        name: `Patient ${abhaId.slice(-4) || "0001"}`,
        date_of_birth: "1990-01-01",
        gender: "Other",
        phone: cleanPhone,
        preferred_language: preferredLang,
        abha_id: abhaId.trim() || null,
      });

      let currentPatId = "PAT-000001";
      if (regRes.success && regRes.data?.patient_id) {
        currentPatId = regRes.data.patient_id;
      }
      setPatientId(currentPatId);

      // Step 2: Create a new intake session
      const sessionRes = await createSession({
        patient_id: currentPatId,
        department: "General Medicine",
      });

      if (sessionRes.success && sessionRes.data?.session_id) {
        setSessionId(sessionRes.data.session_id);
      } else {
        setSessionId(`SES-${Date.now().toString().slice(-6)}`);
      }

      setCurrentStep(1);
      setIsSubmitted(false);
      setLoggedIn(true);
    } catch (err) {
      console.warn("Backend auth failed, proceeding in kiosk session mode:", err);
      setPatientId("PAT-000001");
      setSessionId(`SES-${Date.now().toString().slice(-6)}`);
      setCurrentStep(1);
      setIsSubmitted(false);
      setLoggedIn(true);
    } finally {
      setIsSubmittingLogin(false);
    }
  };

  const handleSubmitCase = async () => {
    setIsSubmittingCase(true);

    try {
      const currentSesId = sessionId || `SES-000001`;

      // 1. Structure the clinical history update payload according to backend API contracts
      const problemLabel = caseData.problemArea
        ? problemAreaSpeech[selectedLanguage]?.[caseData.problemArea] || caseData.problemArea
        : "General Discomfort";

      const historyPayload: ClinicalHistoryUpdatePayload = {
        chief_complaint: {
          value: `${problemLabel}: ${caseData.chiefIssue || "No specific details reported"}`,
          source: { type: "patient_response", source_id: currentSesId },
        },
        history_of_present_illness: {
          duration: {
            value: caseData.duration || "Unspecified",
            source: { type: "patient_response", source_id: currentSesId },
          },
          onset: {
            value: caseData.onset || "Gradual",
            source: { type: "patient_response", source_id: currentSesId },
          },
          severity: {
            value: caseData.severity,
            source: { type: "patient_response", source_id: currentSesId },
          },
          pattern: {
            value: caseData.pattern || "Constant",
            source: { type: "patient_response", source_id: currentSesId },
          },
          triggers: {
            value: caseData.triggers,
            source: { type: "patient_response", source_id: currentSesId },
          },
        },
        past_medical_history: caseData.conditions.map((c) => ({
          condition: c,
          status: "Active",
        })),
        past_surgical_history: caseData.hasPastSurgeries
          ? [{ details: caseData.surgeryDetails || "Previous surgical history reported" }]
          : [],
        current_medications: caseData.takesMedications
          ? [{ details: caseData.medicationDetails || "Active daily medications reported" }]
          : [],
        allergies: caseData.allergies.map((a) => ({
          allergen: a,
        })),
        family_history: caseData.familyConditions.map((f) => ({
          condition: f,
        })),
        personal_history: [
          { type: "diet", value: caseData.diet || "Not specified" },
          { type: "smoking", value: caseData.smoking || "Never" },
          { type: "alcohol", value: caseData.alcohol || "Never" },
          { type: "sleep", value: caseData.sleep || "Good" },
        ],
        review_of_systems: caseData.systemicSymptoms.map((s) => ({
          symptom: s,
          present: true,
        })),
      };

      // Submit history to backend
      await submitClinicalHistory(currentSesId, historyPayload);

      // Trigger AI summary generation
      const sumRes = await generateCaseSummary(currentSesId);
      if (sumRes.success && sumRes.data) {
        setSummaryData(sumRes.data);
      }

      // Mark session as READY_FOR_DOCTOR
      await updateSessionStatus(currentSesId, "READY_FOR_DOCTOR");

      setIsSubmitted(true);
    } catch (err) {
      console.warn("Backend submission fallback:", err);
      setIsSubmitted(true);
    } finally {
      setIsSubmittingCase(false);
    }
  };

  const handleUploadFile = async (file: File) => {
    const currentSesId = sessionId;
    if (!currentSesId) {
      setUploadError("No active session. Please complete login first.");
      return;
    }
    setIsUploading(true);
    setUploadError(null);
    const res = await uploadPatientDocument(currentSesId, file, "medical_report");
    setIsUploading(false);
    if (res.success) {
      if (res.data) {
        setUploadedFiles((prev) => [
          ...prev,
          { name: file.name, docId: res.data.document_id },
        ]);
      }
    } else {
      setUploadError(res.error?.message || "Upload failed. Please try again.");
    }
  };

  const handleOpenTimeline = async () => {
    const currentPatId = patientId;
    if (!currentPatId) return;
    setShowTimeline(true);
    setTimelineLoading(true);
    setTimelineError(null);
    const res = await getPatientTimeline(currentPatId);
    setTimelineLoading(false);
    if (res.success) {
      if (res.data) {
        setTimelineEvents(res.data.events || []);
      }
    } else {
      setTimelineError("Could not load timeline. Backend may be offline.");
    }
  };

  const languages = [
    { key: "English" as Language, name: "English", subtitle: t.englishSub },
    { key: "Hindi" as Language, name: "हिंदी", subtitle: t.hindiSub },
    { key: "Marathi" as Language, name: "मराठी", subtitle: t.marathiSub },
  ];

  const problemAreas = [
    { key: "head", label: t.head },
    { key: "eyes", label: t.eyes },
    { key: "mouth", label: t.mouth },
    { key: "chest", label: t.chest },
    { key: "stomach", label: t.stomach },
    { key: "bones", label: t.bones },
    { key: "hands", label: t.hands },
    { key: "legs", label: t.legs },
    { key: "other", label: t.other },
  ];

  const selectedAreaObj = problemAreas.find((a) => a.key === caseData.problemArea);

  /* ==========================================================================
     SUBMITTED CONFIRMATION SCREEN
     ========================================================================== */
  if (loggedIn && isSubmitted) {
    return (
      <main className="page">
        <div className="kiosk-container">
          <KioskTopBar />

          <div className="success-screen">
            <div className="success-icon-box">✓</div>
            <h2 className="success-title">{t.successTitle}</h2>
            <p className="success-subtitle">{t.successSubtitle}</p>

            <div className="token-badge">
              <div className="token-label">{t.tokenLabel}</div>
              <div className="token-number">A-104</div>
            </div>

            <p style={{ fontWeight: 600, color: "#176158", marginBottom: "28px" }}>
              {t.doctorAssigned}
            </p>

            {summaryData?.summary_text && (
              <div
                style={{
                  maxWidth: "600px",
                  margin: "0 auto 28px",
                  padding: "16px 20px",
                  background: "#f0fdf4",
                  borderRadius: "12px",
                  border: "1px solid #bbf7d0",
                  fontSize: "14px",
                  color: "#166534",
                  textAlign: "left",
                }}
              >
                <strong>AI Clinical Draft:</strong> {summaryData.summary_text}
              </div>
            )}

            <button
              type="button"
              className="next-button"
              style={{ width: "auto", display: "inline-block" }}
              onClick={() => {
                setCaseData(initialCaseData);
                setCurrentStep(1);
                setIsSubmitted(false);
                setLoggedIn(false);
                setPatientId(null);
                setSessionId(null);
                setSummaryData(null);
              }}
            >
              {t.startNew}
            </button>
          </div>
        </div>

        <KioskFooter />
      </main>
    );
  }

  /* ==========================================================================
     QUESTIONNAIRE STEPS 1 TO 14
     ========================================================================== */
  if (loggedIn) {
    return (
      <main className="page">
        <div className="kiosk-container">
          <KioskTopBar />
          <ClinicalStepper currentStep={currentStep} />

          <div className="history-container">
            {/* Context Badge (When available) */}
            {selectedAreaObj && currentStep > 1 && currentStep < 14 && (
              <div className="selected-area-badge">
                <span>{t.selectedAreaLabel}</span>
                <strong>{selectedAreaObj.label}</strong>
              </div>
            )}

            {/* -------------------------------------------------------------
                STEP 1: WHERE IS THE PROBLEM?
            ------------------------------------------------------------- */}
            {currentStep === 1 && (
              <>
                <div className="question-header">
                  <div className="section-tag-row">
                    <span className="section-tag">
                      <span className="status-dot" style={{ width: 6, height: 6 }}></span>
                      {t.step}
                    </span>
                  </div>
                  <h2 className="question-title">{t.problemTitle}</h2>
                  <p className="question-subtitle">{t.problemSubtitle}</p>
                </div>

                <div className="problem-grid">
                  {problemAreas.map((area) => {
                    const isSelected = caseData.problemArea === area.key;
                    return (
                      <button
                        key={area.key}
                        type="button"
                        className={`problem-card ${isSelected ? "selected-problem" : ""}`}
                        onClick={() => handleProblemAreaSelect(area.key)}
                      >
                        <span>{area.label}</span>
                        <span className="problem-check">{isSelected ? "✓" : "→"}</span>
                      </button>
                    );
                  })}
                </div>
              </>
            )}

            {/* -------------------------------------------------------------
                STEP 2: WHAT PROBLEM ARE YOU EXPERIENCING?
            ------------------------------------------------------------- */}
            {currentStep === 2 && (
              <>
                <div className="question-header">
                  <div className="section-tag-row">
                    <span className="section-tag">
                      <span className="status-dot" style={{ width: 6, height: 6 }}></span>
                      {t.step2}
                    </span>
                  </div>
                  <h2 className="question-title">{t.issueTitle}</h2>
                  <p className="question-subtitle">{t.issueSubtitle}</p>
                </div>

                <div className="issue-card">
                  <div className="speak-button-wrap">
                    <button
                      type="button"
                      className={`speak-button ${isListening ? "listening" : ""}`}
                      onClick={() =>
                        toggleListening((transcript) => {
                          updateCase(
                            "chiefIssue",
                            caseData.chiefIssue ? `${caseData.chiefIssue} ${transcript}` : transcript
                          );
                        })
                      }
                    >
                      {isListening ? t.listening : t.speak}
                    </button>
                    <span className="speak-hint">
                      {selectedLanguage === "English"
                        ? "Speak naturally in your preferred language or type below"
                        : selectedLanguage === "Hindi"
                        ? "आप अपनी भाषा में स्वाभाविक रूप से बोल सकते हैं या नीचे लिख सकते हैं"
                        : "तुम्ही तुमच्या भाषेत बोलू शकता किंवा खाली लिहू शकता"}
                    </span>
                  </div>

                  <div className="or-divider">
                    <span>{t.or}</span>
                  </div>

                  <textarea
                    className="issue-textarea"
                    placeholder={t.typePlaceholder}
                    value={caseData.chiefIssue}
                    onChange={(e) => updateCase("chiefIssue", e.target.value)}
                  />
                </div>
              </>
            )}

            {/* -------------------------------------------------------------
                STEP 3: DURATION & ONSET
            ------------------------------------------------------------- */}
            {currentStep === 3 && (
              <>
                <div className="question-header">
                  <div className="section-tag-row">
                    <span className="section-tag">
                      <span className="status-dot" style={{ width: 6, height: 6 }}></span>
                      {t.step3}
                    </span>
                  </div>
                  <h2 className="question-title">{t.durationTitle}</h2>
                  <p className="question-subtitle">{t.durationSubtitle}</p>
                </div>

                <div className="choice-grid" style={{ marginBottom: "24px" }}>
                  {[
                    { key: "< 24h", label: t.dur_24h, sub: t.dur_24h_sub },
                    { key: "1-3d", label: t.dur_3d, sub: t.dur_3d_sub },
                    { key: "1-2w", label: t.dur_2w, sub: t.dur_2w_sub },
                    { key: "1-3m", label: t.dur_1m, sub: t.dur_1m_sub },
                    { key: "> 6m", label: t.dur_6m, sub: t.dur_6m_sub },
                  ].map((item) => {
                    const isSelected = caseData.duration === item.key;
                    return (
                      <button
                        key={item.key}
                        type="button"
                        className={`choice-card ${isSelected ? "selected" : ""}`}
                        onClick={() => updateCase("duration", item.key)}
                      >
                        <div>
                          <div>{item.label}</div>
                          <div className="choice-card-sub">{item.sub}</div>
                        </div>
                        <span className="problem-check" style={{ width: 32, height: 32, fontSize: 14 }}>
                          {isSelected ? "✓" : "→"}
                        </span>
                      </button>
                    );
                  })}
                </div>

                <div className="issue-card" style={{ padding: "20px 24px" }}>
                  <div style={{ fontSize: "12px", fontWeight: 800, color: "#55726e", letterSpacing: "1px", marginBottom: "12px" }}>
                    {t.onsetLabel}
                  </div>
                  <div style={{ display: "flex", gap: "12px" }}>
                    {[
                      { key: "Sudden", label: t.onsetSudden },
                      { key: "Gradual", label: t.onsetGradual },
                    ].map((on) => (
                      <button
                        key={on.key}
                        type="button"
                        className={`yes-no-btn ${caseData.onset === on.key ? "selected" : ""}`}
                        style={{ height: "52px", fontSize: "16px" }}
                        onClick={() => updateCase("onset", on.key)}
                      >
                        {on.label}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* -------------------------------------------------------------
                STEP 4: SEVERITY & PATTERN
            ------------------------------------------------------------- */}
            {currentStep === 4 && (
              <>
                <div className="question-header">
                  <div className="section-tag-row">
                    <span className="section-tag">
                      <span className="status-dot" style={{ width: 6, height: 6 }}></span>
                      {t.step4}
                    </span>
                  </div>
                  <h2 className="question-title">{t.severityTitle}</h2>
                  <p className="question-subtitle">{t.severitySubtitle}</p>
                </div>

                <div className="severity-card" style={{ marginBottom: "20px" }}>
                  <div className="severity-number-display">
                    <div>
                      <span className="severity-value-badge">{caseData.severity}</span>
                      <span style={{ fontSize: "16px", color: "#6a8581", fontWeight: 600 }}> / 10</span>
                    </div>
                    <div className="severity-desc-text">
                      {caseData.severity <= 3 ? t.mild : caseData.severity <= 6 ? t.moderate : t.severe}
                    </div>
                  </div>

                  <div className="severity-scale">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
                      <button
                        key={num}
                        type="button"
                        className={`severity-btn ${caseData.severity === num ? "selected" : ""}`}
                        onClick={() => updateCase("severity", num)}
                      >
                        {num}
                      </button>
                    ))}
                  </div>

                  <div className="severity-labels-row">
                    <span>1 (Mild)</span>
                    <span>5 (Moderate)</span>
                    <span>10 (Severe)</span>
                  </div>
                </div>

                <div className="issue-card" style={{ padding: "20px 24px" }}>
                  <div style={{ fontSize: "12px", fontWeight: 800, color: "#55726e", letterSpacing: "1px", marginBottom: "12px" }}>
                    {t.patternLabel}
                  </div>
                  <div className="choice-grid">
                    {[
                      { key: "constant", label: t.pat_constant },
                      { key: "intermittent", label: t.pat_intermittent },
                      { key: "worsening", label: t.pat_worsening },
                      { key: "improving", label: t.pat_improving },
                    ].map((p) => {
                      const isSelected = caseData.pattern === p.key;
                      return (
                        <button
                          key={p.key}
                          type="button"
                          className={`choice-card ${isSelected ? "selected" : ""}`}
                          style={{ minHeight: "60px" }}
                          onClick={() => updateCase("pattern", p.key)}
                        >
                          <span>{p.label}</span>
                          <span className="problem-check" style={{ width: 28, height: 28, fontSize: 13 }}>
                            {isSelected ? "✓" : "→"}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </>
            )}

            {/* -------------------------------------------------------------
                STEP 5: TRIGGERS & RELIEVING FACTORS
            ------------------------------------------------------------- */}
            {currentStep === 5 && (
              <>
                <div className="question-header">
                  <div className="section-tag-row">
                    <span className="section-tag">
                      <span className="status-dot" style={{ width: 6, height: 6 }}></span>
                      {t.step5}
                    </span>
                  </div>
                  <h2 className="question-title">{t.triggersTitle}</h2>
                  <p className="question-subtitle">{t.triggersSubtitle}</p>
                </div>

                <div className="tags-grid">
                  {[
                    { key: "movement", label: t.trig_movement },
                    { key: "food", label: t.trig_food },
                    { key: "rest", label: t.trig_rest },
                    { key: "stress", label: t.trig_stress },
                    { key: "night", label: t.trig_night },
                    { key: "none", label: t.trig_none },
                  ].map((trig) => {
                    const isSelected = caseData.triggers.includes(trig.key);
                    return (
                      <button
                        key={trig.key}
                        type="button"
                        className={`tag-card ${isSelected ? "selected" : ""}`}
                        onClick={() => toggleArrayItem("triggers", trig.key)}
                      >
                        <span>{trig.label}</span>
                        <span className="tag-check">{isSelected ? "✓" : "+"}</span>
                      </button>
                    );
                  })}
                </div>
              </>
            )}

            {/* -------------------------------------------------------------
                STEP 6: PRE-EXISTING MEDICAL CONDITIONS
            ------------------------------------------------------------- */}
            {currentStep === 6 && (
              <>
                <div className="question-header">
                  <div className="section-tag-row">
                    <span className="section-tag">
                      <span className="status-dot" style={{ width: 6, height: 6 }}></span>
                      {t.step6}
                    </span>
                  </div>
                  <h2 className="question-title">{t.conditionsTitle}</h2>
                  <p className="question-subtitle">{t.conditionsSubtitle}</p>
                </div>

                <div className="tags-grid">
                  {[
                    { key: "diabetes", label: t.cond_diabetes },
                    { key: "bp", label: t.cond_bp },
                    { key: "thyroid", label: t.cond_thyroid },
                    { key: "asthma", label: t.cond_asthma },
                    { key: "heart", label: t.cond_heart },
                    { key: "kidney", label: t.cond_kidney },
                    { key: "none", label: t.cond_none },
                  ].map((cond) => {
                    const isSelected = caseData.conditions.includes(cond.key);
                    return (
                      <button
                        key={cond.key}
                        type="button"
                        className={`tag-card ${isSelected ? "selected" : ""}`}
                        onClick={() => toggleArrayItem("conditions", cond.key)}
                      >
                        <span>{cond.label}</span>
                        <span className="tag-check">{isSelected ? "✓" : "+"}</span>
                      </button>
                    );
                  })}
                </div>
              </>
            )}

            {/* -------------------------------------------------------------
                STEP 7: PAST SURGERIES & HOSPITALIZATIONS
            ------------------------------------------------------------- */}
            {currentStep === 7 && (
              <>
                <div className="question-header">
                  <div className="section-tag-row">
                    <span className="section-tag">
                      <span className="status-dot" style={{ width: 6, height: 6 }}></span>
                      {t.step7}
                    </span>
                  </div>
                  <h2 className="question-title">{t.surgeryTitle}</h2>
                  <p className="question-subtitle">{t.surgerySubtitle}</p>
                </div>

                <div className="yes-no-group">
                  <button
                    type="button"
                    className={`yes-no-btn ${caseData.hasPastSurgeries === true ? "selected" : ""}`}
                    onClick={() => updateCase("hasPastSurgeries", true)}
                  >
                    ✓ {t.yes}
                  </button>
                  <button
                    type="button"
                    className={`yes-no-btn ${caseData.hasPastSurgeries === false ? "selected" : ""}`}
                    onClick={() => {
                      updateCase("hasPastSurgeries", false);
                      updateCase("surgeryDetails", "");
                    }}
                  >
                    ✕ {t.no}
                  </button>
                </div>

                {caseData.hasPastSurgeries === true && (
                  <div className="issue-card">
                    <textarea
                      className="issue-textarea"
                      placeholder={t.surgeryPlaceholder}
                      value={caseData.surgeryDetails}
                      onChange={(e) => updateCase("surgeryDetails", e.target.value)}
                    />
                  </div>
                )}
              </>
            )}

            {/* -------------------------------------------------------------
                STEP 8: CURRENT MEDICATIONS
            ------------------------------------------------------------- */}
            {currentStep === 8 && (
              <>
                <div className="question-header">
                  <div className="section-tag-row">
                    <span className="section-tag">
                      <span className="status-dot" style={{ width: 6, height: 6 }}></span>
                      {t.step8}
                    </span>
                  </div>
                  <h2 className="question-title">{t.medsTitle}</h2>
                  <p className="question-subtitle">{t.medsSubtitle}</p>
                </div>

                <div className="yes-no-group">
                  <button
                    type="button"
                    className={`yes-no-btn ${caseData.takesMedications === true ? "selected" : ""}`}
                    onClick={() => updateCase("takesMedications", true)}
                  >
                    ✓ {t.yes}
                  </button>
                  <button
                    type="button"
                    className={`yes-no-btn ${caseData.takesMedications === false ? "selected" : ""}`}
                    onClick={() => {
                      updateCase("takesMedications", false);
                      updateCase("medicationDetails", "");
                    }}
                  >
                    ✕ {t.no}
                  </button>
                </div>

                {caseData.takesMedications === true && (
                  <div className="issue-card">
                    <textarea
                      className="issue-textarea"
                      placeholder={t.medsPlaceholder}
                      value={caseData.medicationDetails}
                      onChange={(e) => updateCase("medicationDetails", e.target.value)}
                    />
                  </div>
                )}
              </>
            )}

            {/* -------------------------------------------------------------
                STEP 9: KNOWN DRUG & FOOD ALLERGIES
            ------------------------------------------------------------- */}
            {currentStep === 9 && (
              <>
                <div className="question-header">
                  <div className="section-tag-row">
                    <span className="section-tag">
                      <span className="status-dot" style={{ width: 6, height: 6 }}></span>
                      {t.step9}
                    </span>
                  </div>
                  <h2 className="question-title">{t.allergiesTitle}</h2>
                  <p className="question-subtitle">{t.allergiesSubtitle}</p>
                </div>

                <div className="tags-grid">
                  {[
                    { key: "penicillin", label: t.all_penicillin },
                    { key: "painkillers", label: t.all_painkillers },
                    { key: "dust", label: t.all_dust },
                    { key: "food", label: t.all_food },
                    { key: "none", label: t.all_none },
                  ].map((all) => {
                    const isSelected = caseData.allergies.includes(all.key);
                    return (
                      <button
                        key={all.key}
                        type="button"
                        className={`tag-card ${isSelected ? "selected" : ""}`}
                        onClick={() => toggleArrayItem("allergies", all.key)}
                      >
                        <span>{all.label}</span>
                        <span className="tag-check">{isSelected ? "✓" : "+"}</span>
                      </button>
                    );
                  })}
                </div>
              </>
            )}

            {/* -------------------------------------------------------------
                STEP 10: FAMILY MEDICAL HISTORY
            ------------------------------------------------------------- */}
            {currentStep === 10 && (
              <>
                <div className="question-header">
                  <div className="section-tag-row">
                    <span className="section-tag">
                      <span className="status-dot" style={{ width: 6, height: 6 }}></span>
                      {t.step10}
                    </span>
                  </div>
                  <h2 className="question-title">{t.familyTitle}</h2>
                  <p className="question-subtitle">{t.familySubtitle}</p>
                </div>

                <div className="tags-grid">
                  {[
                    { key: "diabetes", label: t.fam_diabetes },
                    { key: "bp", label: t.fam_bp },
                    { key: "heart", label: t.fam_heart },
                    { key: "cancer", label: t.fam_cancer },
                    { key: "stroke", label: t.fam_stroke },
                    { key: "none", label: t.fam_none },
                  ].map((fam) => {
                    const isSelected = caseData.familyConditions.includes(fam.key);
                    return (
                      <button
                        key={fam.key}
                        type="button"
                        className={`tag-card ${isSelected ? "selected" : ""}`}
                        onClick={() => toggleArrayItem("familyConditions", fam.key)}
                      >
                        <span>{fam.label}</span>
                        <span className="tag-check">{isSelected ? "✓" : "+"}</span>
                      </button>
                    );
                  })}
                </div>
              </>
            )}

            {/* -------------------------------------------------------------
                STEP 11: PERSONAL & LIFESTYLE HABITS
            ------------------------------------------------------------- */}
            {currentStep === 11 && (
              <>
                <div className="question-header">
                  <div className="section-tag-row">
                    <span className="section-tag">
                      <span className="status-dot" style={{ width: 6, height: 6 }}></span>
                      {t.step11}
                    </span>
                  </div>
                  <h2 className="question-title">{t.lifestyleTitle}</h2>
                  <p className="question-subtitle">{t.lifestyleSubtitle}</p>
                </div>

                <div className="lifestyle-matrix">
                  {/* Diet */}
                  <div className="lifestyle-card">
                    <div className="lifestyle-label">{t.dietLabel}</div>
                    <div className="lifestyle-options">
                      {[
                        { key: "veg", label: t.diet_veg },
                        { key: "nonveg", label: t.diet_nonveg },
                        { key: "egg", label: t.diet_egg },
                      ].map((d) => (
                        <button
                          key={d.key}
                          type="button"
                          className={`lifestyle-opt-btn ${caseData.diet === d.key ? "selected" : ""}`}
                          onClick={() => updateCase("diet", d.key)}
                        >
                          {d.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Tobacco / Smoking */}
                  <div className="lifestyle-card">
                    <div className="lifestyle-label">{t.smokingLabel}</div>
                    <div className="lifestyle-options">
                      {[
                        { key: "never", label: t.smoke_never },
                        { key: "former", label: t.smoke_former },
                        { key: "active", label: t.smoke_active },
                      ].map((s) => (
                        <button
                          key={s.key}
                          type="button"
                          className={`lifestyle-opt-btn ${caseData.smoking === s.key ? "selected" : ""}`}
                          onClick={() => updateCase("smoking", s.key)}
                        >
                          {s.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Alcohol */}
                  <div className="lifestyle-card">
                    <div className="lifestyle-label">{t.alcoholLabel}</div>
                    <div className="lifestyle-options">
                      {[
                        { key: "never", label: t.alc_never },
                        { key: "occasional", label: t.alc_occasional },
                        { key: "regular", label: t.alc_regular },
                      ].map((a) => (
                        <button
                          key={a.key}
                          type="button"
                          className={`lifestyle-opt-btn ${caseData.alcohol === a.key ? "selected" : ""}`}
                          onClick={() => updateCase("alcohol", a.key)}
                        >
                          {a.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Sleep */}
                  <div className="lifestyle-card">
                    <div className="lifestyle-label">{t.sleepLabel}</div>
                    <div className="lifestyle-options">
                      {[
                        { key: "good", label: t.sleep_good },
                        { key: "disturbed", label: t.sleep_disturbed },
                        { key: "poor", label: t.sleep_poor },
                      ].map((sl) => (
                        <button
                          key={sl.key}
                          type="button"
                          className={`lifestyle-opt-btn ${caseData.sleep === sl.key ? "selected" : ""}`}
                          onClick={() => updateCase("sleep", sl.key)}
                        >
                          {sl.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* -------------------------------------------------------------
                STEP 12: REVIEW OF SYSTEMS (ROS)
            ------------------------------------------------------------- */}
            {currentStep === 12 && (
              <>
                <div className="question-header">
                  <div className="section-tag-row">
                    <span className="section-tag">
                      <span className="status-dot" style={{ width: 6, height: 6 }}></span>
                      {t.step12}
                    </span>
                  </div>
                  <h2 className="question-title">{t.rosTitle}</h2>
                  <p className="question-subtitle">{t.rosSubtitle}</p>
                </div>

                <div className="tags-grid">
                  {[
                    { key: "fever", label: t.ros_fever },
                    { key: "fatigue", label: t.ros_fatigue },
                    { key: "weight", label: t.ros_weight },
                    { key: "dizziness", label: t.ros_dizziness },
                    { key: "cough", label: t.ros_cough },
                    { key: "nausea", label: t.ros_nausea },
                    { key: "none", label: t.ros_none },
                  ].map((r) => {
                    const isSelected = caseData.systemicSymptoms.includes(r.key);
                    return (
                      <button
                        key={r.key}
                        type="button"
                        className={`tag-card ${isSelected ? "selected" : ""}`}
                        onClick={() => toggleArrayItem("systemicSymptoms", r.key)}
                      >
                        <span>{r.label}</span>
                        <span className="tag-check">{isSelected ? "✓" : "+"}</span>
                      </button>
                    );
                  })}
                </div>
              </>
            )}

            {/* -------------------------------------------------------------
                STEP 13: PRIOR REPORTS & RECORDS
            ------------------------------------------------------------- */}
            {currentStep === 13 && (
              <>
                <div className="question-header">
                  <div className="section-tag-row">
                    <span className="section-tag">
                      <span className="status-dot" style={{ width: 6, height: 6 }}></span>
                      {t.step13}
                    </span>
                  </div>
                  <h2 className="question-title">{t.reportsTitle}</h2>
                  <p className="question-subtitle">{t.reportsSubtitle}</p>
                </div>

                <div className="choice-grid" style={{ marginBottom: "20px" }}>
                  {[
                    { key: "abha", label: t.rep_abha, sub: t.rep_abha_sub },
                    { key: "physical", label: t.rep_physical, sub: t.rep_physical_sub },
                    { key: "portal", label: t.rep_portal, sub: t.rep_portal_sub },
                    { key: "none", label: t.rep_none, sub: t.rep_none_sub },
                  ].map((rep) => {
                    const isSelected = caseData.reportStatus === rep.key;
                    return (
                      <button
                        key={rep.key}
                        type="button"
                        className={`choice-card ${isSelected ? "selected" : ""}`}
                        onClick={() => updateCase("reportStatus", rep.key)}
                      >
                        <div>
                          <div>{rep.label}</div>
                          <div className="choice-card-sub">{rep.sub}</div>
                        </div>
                        <span className="problem-check" style={{ width: 32, height: 32, fontSize: 14 }}>
                          {isSelected ? "✓" : "→"}
                        </span>
                      </button>
                    );
                  })}
                </div>

                <div className="issue-card" style={{ padding: "24px" }}>
                  <div style={{ marginBottom: "14px" }}>
                    <div style={{ fontSize: "16px", fontWeight: 700, color: "#113430" }}>
                      📁 {t.uploadTitle}
                    </div>
                    <div style={{ fontSize: "13px", color: "#597773", marginTop: "2px" }}>
                      {t.uploadSubtitle}
                    </div>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    <label
                      htmlFor="medical-doc-upload"
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "10px",
                        padding: "16px 20px",
                        border: "2px dashed #b7ceca",
                        borderRadius: "16px",
                        background: isUploading ? "#f0f7f6" : "#f8faf9",
                        cursor: isUploading ? "not-allowed" : "pointer",
                        transition: "all 0.2s ease",
                      }}
                    >
                      <input
                        id="medical-doc-upload"
                        type="file"
                        accept=".pdf,.jpg,.jpeg,.png,.txt,application/pdf,image/*"
                        style={{ display: "none" }}
                        disabled={isUploading}
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) {
                            updateCase("reportStatus", "portal");
                            handleUploadFile(file);
                          }
                          e.target.value = "";
                        }}
                      />
                      <span style={{ fontSize: "20px" }}>📄</span>
                      <span style={{ fontSize: "15px", fontWeight: 700, color: "#176158" }}>
                        {isUploading ? t.uploading : t.uploadButton}
                      </span>
                    </label>

                    {uploadError && (
                      <div className="login-error" style={{ margin: 0 }}>
                        ⚠️ {uploadError}
                      </div>
                    )}

                    {uploadedFiles.length > 0 && (
                      <div style={{ marginTop: "6px" }}>
                        <div style={{ fontSize: "12px", fontWeight: 700, color: "#55726e", letterSpacing: "0.5px", textTransform: "uppercase", marginBottom: "8px" }}>
                          {t.uploadedTitle} ({uploadedFiles.length})
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                          {uploadedFiles.map((file, idx) => (
                            <div
                              key={idx}
                              style={{
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "space-between",
                                padding: "10px 14px",
                                background: "#edf7f4",
                                border: "1px solid #b7ceca",
                                borderRadius: "12px",
                                fontSize: "14px",
                                color: "#176158",
                                fontWeight: 600,
                              }}
                            >
                              <div style={{ display: "flex", alignItems: "center", gap: "8px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                <span>✓</span>
                                <span style={{ textOverflow: "ellipsis", overflow: "hidden" }}>{file.name}</span>
                              </div>
                              <span style={{ fontSize: "11px", color: "#52716d", padding: "2px 8px", background: "#ffffff", borderRadius: "8px", border: "1px solid #d4dfdd", flexShrink: 0 }}>
                                {file.docId}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}

            {/* -------------------------------------------------------------
                STEP 14: CASE SUMMARY & CONFIRMATION
            ------------------------------------------------------------- */}
            {currentStep === 14 && (
              <>
                <div className="question-header">
                  <div className="section-tag-row">
                    <span className="section-tag">
                      <span className="status-dot" style={{ width: 6, height: 6 }}></span>
                      {t.step14}
                    </span>
                  </div>
                  <h2 className="question-title">{t.summaryTitle}</h2>
                  <p className="question-subtitle">{t.summarySubtitle}</p>
                </div>

                <div className="summary-container">
                  {/* Summary Header Banner */}
                  <div className="summary-header-card">
                    <div>
                      <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "1px", opacity: 0.85, textTransform: "uppercase" }}>
                        ABHA PATIENT IDENTIFIER
                      </div>
                      <div className="summary-patient-id">
                        {patientId ? `${patientId} · ABHA: ${abhaId}` : abhaId || "11-1111-1111-1111"}
                      </div>
                    </div>
                    <div className="summary-badge-status">
                      ● FHIR CLINICAL DRAFT READY
                    </div>
                  </div>

                  {/* Summary Grid */}
                  <div className="summary-grid">
                    {/* Chief Complaint */}
                    <div className="summary-section-card">
                      <div className="summary-section-title">📍 1. CHIEF COMPLAINT</div>
                      <div className="summary-content-text">
                        <strong>Area:</strong> {selectedAreaObj?.label || "Not specified"}
                      </div>
                      <div className="summary-content-text" style={{ marginTop: "4px" }}>
                        <strong>Issue:</strong> {caseData.chiefIssue || "None recorded"}
                      </div>
                    </div>

                    {/* History / Duration */}
                    <div className="summary-section-card">
                      <div className="summary-section-title">⏱️ 2. PRESENT ILLNESS</div>
                      <div className="summary-content-text">
                        <strong>Duration:</strong> {caseData.duration || "Not specified"} ({caseData.onset || "Unknown onset"})
                      </div>
                      <div className="summary-content-text" style={{ marginTop: "4px" }}>
                        <strong>Severity:</strong> {caseData.severity}/10 · Pattern: {caseData.pattern || "Not specified"}
                      </div>
                    </div>

                    {/* Medical History */}
                    <div className="summary-section-card">
                      <div className="summary-section-title">🩺 3. PAST MEDICAL HISTORY</div>
                      <div className="summary-pill-list">
                        {caseData.conditions.length > 0
                          ? caseData.conditions.map((c) => <span key={c} className="summary-pill">{c}</span>)
                          : <span className="summary-pill">None Reported</span>}
                      </div>
                      <div className="summary-content-text" style={{ marginTop: "6px" }}>
                        <strong>Surgeries:</strong> {caseData.hasPastSurgeries ? (caseData.surgeryDetails || "Yes") : "No"}
                      </div>
                    </div>

                    {/* Drugs & Allergies */}
                    <div className="summary-section-card">
                      <div className="summary-section-title">💊 4. MEDICATIONS & ALLERGIES</div>
                      <div className="summary-content-text">
                        <strong>Medications:</strong> {caseData.takesMedications ? (caseData.medicationDetails || "Yes") : "None"}
                      </div>
                      <div className="summary-pill-list">
                        {caseData.allergies.length > 0
                          ? caseData.allergies.map((a) => <span key={a} className="summary-pill">{a}</span>)
                          : <span className="summary-pill">No Known Allergies</span>}
                      </div>
                    </div>

                    {/* Family & Personal */}
                    <div className="summary-section-card">
                      <div className="summary-section-title">👨‍👩‍👧 5. FAMILY & LIFESTYLE</div>
                      <div className="summary-content-text">
                        <strong>Family:</strong> {caseData.familyConditions.join(", ") || "None"}
                      </div>
                      <div className="summary-content-text" style={{ marginTop: "4px" }}>
                        <strong>Diet:</strong> {caseData.diet || "-"} · <strong>Smoke:</strong> {caseData.smoking || "-"} · <strong>Sleep:</strong> {caseData.sleep || "-"}
                      </div>
                    </div>

                    {/* ROS & Reports */}
                    <div className="summary-section-card">
                      <div className="summary-section-title">📋 6. ROS & RECORDS</div>
                      <div className="summary-pill-list">
                        {caseData.systemicSymptoms.length > 0
                          ? caseData.systemicSymptoms.map((s) => <span key={s} className="summary-pill">{s}</span>)
                          : <span className="summary-pill">No Systemic Symptoms</span>}
                      </div>
                      <div className="summary-content-text" style={{ marginTop: "6px" }}>
                        <strong>Records:</strong> {caseData.reportStatus || "Not specified"}
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* -------------------------------------------------------------
                PERSISTENT NAVIGATION BUTTONS
            ------------------------------------------------------------- */}
            <div className="navigation-buttons">
              <button
                type="button"
                className="back-button"
                onClick={() => {
                  if (currentStep === 1) {
                    setLoggedIn(false);
                  } else {
                    setCurrentStep((prev) => prev - 1);
                  }
                }}
              >
                {t.back}
              </button>

              {currentStep < 14 ? (
                <button
                  type="button"
                  className="next-button"
                  disabled={
                    (currentStep === 1 && !caseData.problemArea) ||
                    (currentStep === 2 && !caseData.chiefIssue.trim())
                  }
                  onClick={() => setCurrentStep((prev) => prev + 1)}
                >
                  {t.next}
                </button>
              ) : (
                <button
                  type="button"
                  className="next-button"
                  disabled={isSubmittingCase}
                  style={{ background: "linear-gradient(135deg, #10b981, #059669)" }}
                  onClick={handleSubmitCase}
                >
                  {isSubmittingCase ? t.submittingCase : t.submitCase}
                </button>
              )}
            </div>
          </div>
        </div>

        <KioskFooter />
      </main>
    );
  }

  /* ==========================================================================
     LOGIN SCREEN
     ========================================================================== */
  return (
    <main className="page">
      <div className="kiosk-container">
        <KioskTopBar />

        <div className="login-header">
          <div className="login-badge">STATION-04 &nbsp; OPD PATIENT KIOSK</div>
          <h1>MediKiosk</h1>
          <h2>{t.greeting}</h2>
          <p>{t.chooseLanguage}</p>
        </div>

        <div className="language-grid">
          {languages.map((lang) => {
            const isSelected = selectedLanguage === lang.key;
            return (
              <button
                key={lang.key}
                type="button"
                className={`language-card ${isSelected ? "selected" : ""}`}
                onClick={() => handleLanguageSelect(lang.key)}
              >
                <div>
                  <h2>{lang.name}</h2>
                  <p>{lang.subtitle}</p>
                </div>
                <div className="language-icon">
                  {isSelected ? "✓" : "→"}
                </div>
              </button>
            );
          })}
        </div>

        <div className="login-card">
          <label>{t.abhaLabel}</label>

          <div className="login-row">
            <input
              type="text"
              value={abhaId}
              onChange={(e) => setAbhaId(e.target.value)}
              placeholder={t.abhaPlaceholder}
              disabled={isSubmittingLogin}
            />

            <input
              className="passcode"
              type="password"
              value={passcode}
              onChange={(e) => setPasscode(e.target.value)}
              placeholder={t.passcode}
              disabled={isSubmittingLogin}
            />

            <button
              type="button"
              className="login-button"
              onClick={handleLogin}
              disabled={isSubmittingLogin}
            >
              {isSubmittingLogin ? t.loggingIn : t.login}
            </button>
          </div>

          {loginError && <p className="login-error">{loginError}</p>}

          <p className="testing-text">
            <span>ℹ️</span> {t.testing}
          </p>

          <div className="divider"></div>

          <div className="bottom-options">
            <button
              type="button"
              onClick={() => setAyushActive(!ayushActive)}
            >
              {ayushActive ? t.ayushOn : t.ayush}
            </button>
            <button
              type="button"
              onClick={() => router.push("/doctor/login")}
              title="Navigate to Doctor Login Portal"
            >
              {t.doctor}
            </button>
            <button
              type="button"
              disabled
              title="Timeline will be available after history taking"
            >
              {t.timeline}
            </button>
          </div>
        </div>
      </div>

      <KioskFooter />
    </main>
  );
}
