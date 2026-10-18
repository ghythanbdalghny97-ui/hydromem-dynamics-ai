# ============================================================
# HYDROMEM Dynamics AI v15.6
# Global Configuration
# ============================================================


# ------------------------------------------------------------
# معلومات المنصة
# ------------------------------------------------------------

APP_NAME = "HYDROMEM Dynamics AI"

APP_VERSION = "v15.6"

APP_DESCRIPTION = (
    "منصة محاكاة حاسوبية للأنظمة المعقدة "
    "والنمذجة الديناميكية والذكاء الاصطناعي"
)


# ------------------------------------------------------------
# أنواع الحسابات
# ------------------------------------------------------------

ACCOUNT_TYPES = {

    "individual":
        "👤 فردي",

    "researcher":
        "🔬 باحث",

    "laboratory":
        "🧪 مختبر",

    "university":
        "🎓 جامعة",

    "hospital":
        "🏥 مستشفى",

    "enterprise":
        "🏢 شركة"

}



# ------------------------------------------------------------
# خطط الاشتراك
# ------------------------------------------------------------

PLANS = {


    "individual": {

        "name_ar":
            "👤 فردي",

        "price_m":
            19,

        "users":
            1,

        "storage_mb":
            100,

        "ai_requests_day":
            50,

        "models":
            [
                "dynamic_model"
            ]

    },



    "researcher": {


        "name_ar":
            "🔬 باحث",

        "price_m":
            79,

        "users":
            1,

        "storage_mb":
            1000,

        "ai_requests_day":
            300,

        "models":
            [
                "dynamic_model",
                "hydromem",
                "tbp"
            ]

    },



    "laboratory": {


        "name_ar":
            "🧪 مختبر",

        "price_m":
            299,

        "users":
            5,

        "storage_mb":
            10000,

        "ai_requests_day":
            1500,

        "models":
            [
                "all"
            ]

    },



    "university": {


        "name_ar":
            "🎓 جامعة",

        "price_m":
            1500,

        "users":
            50,

        "storage_mb":
            100000,

        "ai_requests_day":
            10000,

        "models":
            [
                "all"
            ]

    },



    "hospital": {


        "name_ar":
            "🏥 مستشفى",

        "price_m":
            2500,

        "users":
            100,

        "storage_mb":
            200000,

        "ai_requests_day":
            20000,

        "models":
            [
                "biomedical",
                "dynamic",
                "analysis"
            ]

    },



    "enterprise": {


        "name_ar":
            "🏢 شركة",

        "price_m":
            5000,

        "users":
            9999,

        "storage_mb":
            1000000,

        "ai_requests_day":
            100000,

        "models":
            [
                "all"
            ]

    }

}



# ------------------------------------------------------------
# النماذج العلمية المتاحة
# ------------------------------------------------------------

SCIENTIFIC_MODELS = {


    "dynamic_model": {

        "name":
            "General Dynamic System",

        "status":
            "available"

    },


    "hydromem": {

        "name":
            "HYDROMEM-BIO Model",

        "status":
            "research prototype"

    },


    "tbp": {

        "name":
            "Tension Balance Protocol",

        "status":
            "research prototype"

    },


    "biomedical": {

        "name":
            "Biomedical Simulation",

        "status":
            "development"

    }

}



# ------------------------------------------------------------
# إعدادات الذكاء الاصطناعي
# ------------------------------------------------------------

AI_CONFIG = {

    "default_language":
        "Arabic",

    "max_tokens":
        4096,

    "latex_enabled":
        True,

    "scientific_mode":
        True

}



# ------------------------------------------------------------
# إعدادات الملفات
# ------------------------------------------------------------

FILE_CONFIG = {

    "allowed_extensions":
        [
            "pdf",
            "png",
            "jpg",
            "jpeg",
            "csv",
            "txt"
        ],


    "max_file_size_mb":
        20

}



# ------------------------------------------------------------
# حقوق الملكية
# ------------------------------------------------------------

COPYRIGHT = {

    "owner":
        "Abdul Ghani Saleh Mohsen Mohamed Ghaithan",

    "project":
        "HYDROMEM Dynamics AI",

    "license":
        "Research Prototype - All Rights Reserved"

}
